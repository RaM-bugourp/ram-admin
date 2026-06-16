"""Test AIService — mock mode, failover chain, rate limit."""
import pytest
from unittest.mock import patch, MagicMock
from django.test import override_settings

from apps.ai.services.ai_service import AIService, get_ai_service, check_rate_limit
from apps.ai.services.ai_errors import AIAllProvidersFailedError, AIRateLimitError
from apps.ai.services.ai_failover import CircuitBreakerRegistry


# ── Mock 模式（无任何 Provider Key）──────────────────────────────

class TestAIServiceMockMode:
    """未配置 Key 时走 Mock 回复."""

    def setup_method(self):
        AIService._instance = None
        CircuitBreakerRegistry._instance = None

    @override_settings(AI_PROVIDERS=[], AI_MOCK_WHEN_NO_KEY=True)
    def test_mock_mode_returns_reply(self):
        svc = AIService()
        reply, provider, failover = svc.chat(
            [{"role": "user", "content": "你好"}], context="测试"
        )
        assert provider == "mock"
        assert failover is False
        assert "Mock" in reply

    @override_settings(AI_PROVIDERS=[], AI_MOCK_WHEN_NO_KEY=False)
    def test_no_mock_raises_error(self):
        svc = AIService()
        with pytest.raises(AIAllProvidersFailedError):
            svc.chat([{"role": "user", "content": "hi"}])

    @override_settings(AI_PROVIDERS=[], AI_MOCK_WHEN_NO_KEY=True)
    def test_mock_extracts_last_user_message(self):
        svc = AIService()
        messages = [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "我的问题"},
        ]
        reply, _, _ = svc.chat(messages, context="ctx")
        assert "我的问题" in reply


# ── 故障转移链 ──────────────────────────────────────────────────

class TestAIServiceFailover:
    """多 Provider 自动故障转移."""

    def setup_method(self):
        AIService._instance = None
        CircuitBreakerRegistry._instance = None

    @override_settings(
        AI_PROVIDERS=[
            {"name": "openai", "api_key": "sk-1", "base_url": "https://x", "model": "gpt-4"},
            {"name": "deepseek", "api_key": "sk-2", "base_url": "https://y", "model": "ds-v3"},
        ],
        AI_FAILOVER_FAILURE_THRESHOLD=3,
        AI_FAILOVER_RECOVERY_TIMEOUT=60,
    )
    @patch("apps.ai.services.ai_service.call_chat")
    def test_first_provider_succeeds(self, mock_call):
        mock_call.return_value = "AI reply"
        svc = AIService()
        reply, provider, failover = svc.chat([{"role": "user", "content": "hi"}])
        assert reply == "AI reply"
        assert failover is False

    @override_settings(
        AI_PROVIDERS=[
            {"name": "openai", "api_key": "sk-1", "base_url": "https://x", "model": "gpt-4"},
            {"name": "deepseek", "api_key": "sk-2", "base_url": "https://y", "model": "ds-v3"},
        ],
        AI_FAILOVER_FAILURE_THRESHOLD=3,
        AI_FAILOVER_RECOVERY_TIMEOUT=60,
    )
    @patch("apps.ai.services.ai_service.call_chat")
    def test_failover_to_second_provider(self, mock_call):
        from apps.ai.services.ai_errors import AIProviderError
        # 第一次调用失败，第二次成功
        mock_call.side_effect = [
            AIProviderError("openai", "timeout"),
            "fallback reply",
        ]
        svc = AIService()
        reply, provider, failover = svc.chat([{"role": "user", "content": "hi"}])
        assert failover is True
        assert reply == "fallback reply"

    @override_settings(
        AI_PROVIDERS=[
            {"name": "openai", "api_key": "sk-1", "base_url": "https://x", "model": "gpt-4"},
            {"name": "deepseek", "api_key": "sk-2", "base_url": "https://y", "model": "ds-v3"},
        ],
        AI_FAILOVER_FAILURE_THRESHOLD=3,
        AI_FAILOVER_RECOVERY_TIMEOUT=60,
    )
    @patch("apps.ai.services.ai_service.call_chat")
    def test_all_providers_fail(self, mock_call):
        from apps.ai.services.ai_errors import AIProviderError
        mock_call.side_effect = AIProviderError("any", "fail")
        svc = AIService()
        with pytest.raises(AIAllProvidersFailedError):
            svc.chat([{"role": "user", "content": "hi"}])


# ── get_status ────────────────────────────────────────────────────

class TestAIServiceGetStatus:
    """Provider 状态查询."""

    def setup_method(self):
        AIService._instance = None
        CircuitBreakerRegistry._instance = None

    @override_settings(AI_PROVIDERS=[], AI_MOCK_WHEN_NO_KEY=True)
    def test_status_in_mock_mode(self):
        svc = AIService()
        status = svc.get_status()
        assert status["mock_mode"] is True
        assert status["current_provider"] == "mock"

    @override_settings(
        AI_PROVIDERS=[
            {"name": "openai", "api_key": "sk-1", "base_url": "https://x", "model": "gpt-4"},
        ],
        AI_FAILOVER_FAILURE_THRESHOLD=3,
        AI_FAILOVER_RECOVERY_TIMEOUT=60,
    )
    def test_status_with_provider(self):
        svc = AIService()
        status = svc.get_status()
        assert status["mock_mode"] is False
        assert len(status["providers"]) == 1
        assert status["providers"][0]["name"] == "openai"


# ── get_ai_service 工厂 ─────────────────────────────────────────

class TestGetAIService:
    """get_ai_service 单例工厂."""

    def setup_method(self):
        AIService._instance = None
        CircuitBreakerRegistry._instance = None
        import apps.ai.services.ai_service as mod
        mod._ai_service = None

    def test_returns_singleton(self):
        s1 = get_ai_service()
        s2 = get_ai_service()
        assert s1 is s2


# ── 频次限制 ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRateLimit:
    """check_rate_limit 频次控制."""

    @override_settings(AI_RATE_LIMIT_PER_ROOT=100, AI_RATE_LIMIT_PER_AGENT=20)
    def test_under_limit_passes(self, root_user):
        # 0 条记录，不应报错
        check_rate_limit(root_user.id, is_agent=False)

    @override_settings(AI_RATE_LIMIT_PER_ROOT=0)
    def test_over_limit_raises(self, root_user):
        with pytest.raises(AIRateLimitError):
            check_rate_limit(root_user.id, is_agent=False)
