"""Core AI service — multi-provider failover chat."""
import logging
import threading
from typing import Optional

from django.conf import settings
from django.utils import timezone

from apps.ai.services.ai_client import call_chat
from apps.ai.services.ai_errors import (
    AIAllProvidersFailedError,
    AIProviderError,
    AIRateLimitError,
)
from apps.ai.services.ai_failover import (
    CircuitBreakerRegistry,
    ProviderConfig,
    get_active_providers,
    has_any_provider,
)

logger = logging.getLogger(__name__)


class AIService:
    """多 Provider 自动故障转移 AI 服务.

    线程安全的单例：内部状态（当前基准 Provider 索引）受锁保护。
    """

    _instance: Optional['AIService'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._current_index = 0
                    cls._instance._state_lock = threading.Lock()
        return cls._instance

    # ── 对外主入口 ────────────────────────────────────────────

    def chat(self, messages: list[dict], *, context: str = '',
             temperature: float = 0.7) -> tuple[str, str, bool]:
        """对话主入口.

        Returns:
            (reply, provider_used, failover_triggered)

        Raises:
            AIAllProvidersFailedError: 所有 Provider 均失败
        """
        # 1) 频次检查（root 维度由 view 层注入 user 后做）
        #    — 这里只负责纯调用

        # 2) 无任何可用 Provider 时进入 Mock 模式
        if not has_any_provider():
            if getattr(settings, 'AI_MOCK_WHEN_NO_KEY', True):
                return self._mock_reply(messages, context), 'mock', False
            raise AIAllProvidersFailedError('未配置任何 AI Provider Key')

        # 3) 依次尝试 Provider，自动故障转移
        tried = []
        failover_triggered = False
        providers = get_active_providers()
        registry = CircuitBreakerRegistry()
        registry.ensure_initialized()

        start_idx = self._current_index % len(providers)

        for offset in range(len(providers)):
            idx = (start_idx + offset) % len(providers)
            config = providers[idx]
            breaker = registry.get(config.name)

            if not breaker.can_use():
                logger.info("Provider '%s' 被熔断，跳过", config.name)
                continue

            tried.append(config.name)
            try:
                reply = call_chat(config, messages, temperature=temperature)
                breaker.record_success()
                # 成功则切换基准 Provider
                with self._state_lock:
                    self._current_index = idx
                logger.info("AI chat via '%s' (failover=%s)", config.name, failover_triggered)
                return reply, config.name, failover_triggered
            except AIProviderError as e:
                breaker.record_failure()
                failover_triggered = True
                logger.warning("Provider '%s' 失败，尝试切换: %s", config.name, e.message)
                # 异步通知 root（非阻塞）
                self._alert_root_async(config.name, e.message)
                continue
            except Exception as e:  # noqa: BLE001
                breaker.record_failure()
                failover_triggered = True
                logger.exception("Provider '%s' 未知异常: %s", config.name, e)
                self._alert_root_async(config.name, str(e))
                continue

        raise AIAllProvidersFailedError(f"所有 Provider 失败: {tried}")

    @property
    def _current_index(self) -> int:
        return self.__dict__.get('_current_index', 0)

    @_current_index.setter
    def _current_index(self, v: int):
        self.__dict__['_current_index'] = v

    # ── Provider 状态查询 ────────────────────────────────────

    def get_status(self) -> dict:
        """返回当前 Provider 池状态（供前端告警组件使用）."""
        registry = CircuitBreakerRegistry()
        registry.ensure_initialized()
        breakers = {b['name']: b for b in registry.all_status()}
        providers = []
        active_name = ''
        for p in get_active_providers():
            providers.append({
                'name': p.name,
                'model': p.model,
                **breakers.get(p.name, {'status': 'healthy', 'failures': 0}),
            })
            if not active_name and breakers.get(p.name, {}).get('status') != 'failed':
                active_name = p.name

        if not providers and getattr(settings, 'AI_MOCK_WHEN_NO_KEY', True):
            active_name = 'mock'
            providers = [{'name': 'mock', 'model': 'local-mock', 'status': 'healthy', 'failures': 0}]

        failover_triggered = any(
            b.get('status') in ('failed', 'degraded') for b in breakers.values()
        )

        return {
            'providers': providers,
            'current_provider': active_name,
            'failover_triggered': failover_triggered,
            'mock_mode': active_name == 'mock',
        }

    # ── 内部辅助 ──────────────────────────────────────────────

    def _mock_reply(self, messages: list[dict], context: str) -> str:
        """未配置 Key 时的本地占位回复（方便开发联调）."""
        last_user = ''
        for m in reversed(messages):
            if m.get('role') == 'user':
                last_user = m.get('content', '')
                break
        return (
            "## 🤖 Mock 模式\n\n"
            "当前未配置任何 AI Provider 的 API Key，系统运行在本地占位模式。\n\n"
            f"**你的提问：** {last_user or '（空）'}\n\n"
            "配置 `.env` 中的 `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` / `QCLAW_API_KEY` "
            "即可启用真实 AI 对话。\n\n"
            f"_上下文: {context or '无'}_"
        )

    def _alert_root_async(self, failed_provider: str, error: str):
        """非阻塞通知所有 root 用户."""
        import threading as _t

        def _run():
            try:
                from apps.ai.services.notification_service import NotificationService
                NotificationService.alert_provider_failure(failed_provider, error)
            except Exception as e:  # noqa: BLE001 — 告警失败不应影响主流程
                logger.warning("Provider 告警发送失败: %s", e)

        _t.Thread(target=_run, daemon=True).start()


# 便利单例访问
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


# ── 频次限制工具 ────────────────────────────────────────────

def check_rate_limit(user_id: int, is_agent: bool = False) -> None:
    """检查当天调用频次是否超限."""
    from apps.ai.models import AICallLog
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if is_agent:
        limit = settings.AI_RATE_LIMIT_PER_AGENT
        used = AICallLog.objects.filter(
            agent_id__gt='', created_at__gte=today_start
        ).count()
    else:
        limit = settings.AI_RATE_LIMIT_PER_ROOT
        used = AICallLog.objects.filter(
            root_user_id=user_id, created_at__gte=today_start
        ).count()

    if used >= limit:
        raise AIRateLimitError(f"今日调用已达上限 ({used}/{limit})")
