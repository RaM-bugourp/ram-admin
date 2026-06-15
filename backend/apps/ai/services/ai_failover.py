"""Provider failover — circuit breaker + provider config."""
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class ProviderStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class ProviderConfig:
    """单个 AI Provider 配置."""

    name: str                # 'openai' | 'deepseek' | 'qclaw' | ...
    api_key: str
    base_url: str
    model: str
    timeout: int = 30

    @property
    def usable(self) -> bool:
        """是否已配置有效 Key."""
        return bool(self.api_key)


class CircuitBreaker:
    """熔断器 — 连续失败 N 次后标记 FAILED，恢复时间过后进入半开状态."""

    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._lock = threading.Lock()
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.status = ProviderStatus.HEALTHY

    def record_failure(self) -> None:
        with self._lock:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                if self.status != ProviderStatus.FAILED:
                    logger.warning(
                        "Provider '%s' circuit breaker OPENED (failures=%d)",
                        self.name, self.failures,
                    )
                self.status = ProviderStatus.FAILED

    def record_success(self) -> None:
        with self._lock:
            self.failures = 0
            self.last_failure_time = None
            self.status = ProviderStatus.HEALTHY

    def can_use(self) -> bool:
        """是否允许调用：HEALTHY 直接可用；FAILED 超过恢复时间进入 DEGRADED 半开."""
        with self._lock:
            if self.status == ProviderStatus.HEALTHY:
                return True
            if self.status == ProviderStatus.DEGRADED:
                return True
            # FAILED — 检查恢复窗口
            if self.last_failure_time is not None:
                elapsed = time.time() - self.last_failure_time
                if elapsed > self.recovery_timeout:
                    self.status = ProviderStatus.DEGRADED
                    logger.info("Provider '%s' entering half-open (DEGRADED)", self.name)
                    return True
            return False

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'status': self.status.value,
            'failures': self.failures,
            'last_failure_time': self.last_failure_time,
        }


class CircuitBreakerRegistry:
    """全局熔断器注册表（线程安全单例）."""

    _instance: Optional['CircuitBreakerRegistry'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._breakers = {}
                    cls._instance._initialized = False
        return cls._instance

    def ensure_initialized(self) -> None:
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            for p in load_providers():
                if p.name not in self._breakers:
                    self._breakers[p.name] = CircuitBreaker(
                        name=p.name,
                        failure_threshold=settings.AI_FAILOVER_FAILURE_THRESHOLD,
                        recovery_timeout=settings.AI_FAILOVER_RECOVERY_TIMEOUT,
                    )
            self._initialized = True

    def get(self, name: str) -> CircuitBreaker:
        self.ensure_initialized()
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name=name)
        return self._breakers[name]

    def all_status(self) -> list[dict]:
        self.ensure_initialized()
        return [b.to_dict() for b in self._breakers.values()]


# ── Provider 加载 ─────────────────────────────────────────────────

@dataclass
class _LoadResult:
    providers: list = field(default_factory=list)


def load_providers() -> list[ProviderConfig]:
    """从 settings.AI_PROVIDERS 加载可用 Provider 列表（仅保留已配置 Key 的）."""
    configs = []
    for p in getattr(settings, 'AI_PROVIDERS', []):
        cfg = ProviderConfig(
            name=p['name'],
            api_key=p.get('api_key', ''),
            base_url=p['base_url'],
            model=p['model'],
            timeout=getattr(settings, 'AI_TIMEOUT', 30),
        )
        configs.append(cfg)
    return configs


def get_active_providers() -> list[ProviderConfig]:
    """返回已配置 Key 的 Provider（按 settings 中的优先级顺序）."""
    return [p for p in load_providers() if p.usable]


def has_any_provider() -> bool:
    return any(p.usable for p in load_providers())


def get_breaker_registry() -> CircuitBreakerRegistry:
    reg = CircuitBreakerRegistry()
    reg.ensure_initialized()
    return reg
