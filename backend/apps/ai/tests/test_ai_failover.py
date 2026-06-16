"""Test CircuitBreaker — three-state transition, thread safety, Provider loading."""
import time
import threading

import pytest
from django.test import override_settings

from apps.ai.services.ai_failover import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    ProviderConfig,
    ProviderStatus,
    load_providers,
    get_active_providers,
    has_any_provider,
)


# ── ProviderConfig ──────────────────────────────────────────────

class TestProviderConfig:
    """ProviderConfig.usable 判定."""

    def test_usable_with_key(self):
        cfg = ProviderConfig(name="test", api_key="sk-xxx", base_url="https://x", model="gpt-4")
        assert cfg.usable is True

    def test_not_usable_without_key(self):
        cfg = ProviderConfig(name="test", api_key="", base_url="https://x", model="gpt-4")
        assert cfg.usable is False

    def test_default_timeout(self):
        cfg = ProviderConfig(name="t", api_key="k", base_url="u", model="m")
        assert cfg.timeout == 30

    def test_custom_timeout(self):
        cfg = ProviderConfig(name="t", api_key="k", base_url="u", model="m", timeout=60)
        assert cfg.timeout == 60


# ── CircuitBreaker 三态转换 ────────────────────────────────────

class TestCircuitBreaker:
    """熔断器 HEALTHY → FAILED → DEGRADED → HEALTHY."""

    def test_initial_state_healthy(self):
        cb = CircuitBreaker(name="test")
        assert cb.status == ProviderStatus.HEALTHY
        assert cb.failures == 0
        assert cb.can_use() is True

    def test_record_failure_increments(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        cb.record_failure()
        assert cb.failures == 1
        assert cb.status == ProviderStatus.HEALTHY  # 还没到阈值

    def test_open_after_threshold(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.status == ProviderStatus.FAILED
        assert cb.can_use() is False

    def test_success_resets_to_healthy(self):
        cb = CircuitBreaker(name="test", failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.status == ProviderStatus.FAILED
        cb.record_success()
        assert cb.status == ProviderStatus.HEALTHY
        assert cb.failures == 0

    def test_degraded_after_recovery_timeout(self):
        cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=0)
        cb.record_failure()
        cb.record_failure()
        assert cb.status == ProviderStatus.FAILED
        # recovery_timeout=0 → 立刻进入半开
        time.sleep(0.01)
        assert cb.can_use() is True
        assert cb.status == ProviderStatus.DEGRADED

    def test_to_dict(self):
        cb = CircuitBreaker(name="test")
        d = cb.to_dict()
        assert d["name"] == "test"
        assert d["status"] == "healthy"
        assert d["failures"] == 0


# ── 线程安全 ────────────────────────────────────────────────────

class TestCircuitBreakerThreadSafety:
    """多线程并发 record_failure 不丢计数."""

    def test_concurrent_failures(self):
        cb = CircuitBreaker(name="test", failure_threshold=100)
        threads = []
        for _ in range(10):
            t = threading.Thread(target=lambda: cb.record_failure())
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        assert cb.failures == 10


# ── CircuitBreakerRegistry 单例 ─────────────────────────────────

class TestCircuitBreakerRegistry:
    """全局注册表单例 + 初始化."""

    def setup_method(self):
        # 每个测试前重置单例，避免状态污染
        CircuitBreakerRegistry._instance = None

    def test_singleton(self):
        r1 = CircuitBreakerRegistry()
        r2 = CircuitBreakerRegistry()
        assert r1 is r2

    @override_settings(
        AI_PROVIDERS=[
            {"name": "openai", "api_key": "sk-test", "base_url": "https://x", "model": "gpt-4"},
        ],
        AI_FAILOVER_FAILURE_THRESHOLD=3,
        AI_FAILOVER_RECOVERY_TIMEOUT=60,
    )
    def test_ensure_initialized_creates_breakers(self):
        reg = CircuitBreakerRegistry()
        reg.ensure_initialized()
        b = reg.get("openai")
        assert b is not None
        assert b.name == "openai"

    def test_get_unknown_provider_creates_new(self):
        reg = CircuitBreakerRegistry()
        b = reg.get("nonexistent_provider")
        assert b is not None
        assert b.name == "nonexistent_provider"

    @override_settings(AI_PROVIDERS=[])
    def test_all_status_empty(self):
        reg = CircuitBreakerRegistry()
        reg.ensure_initialized()
        status = reg.all_status()
        assert isinstance(status, list)


# ── Provider 加载 ───────────────────────────────────────────────

class TestProviderLoading:
    """load_providers / get_active_providers / has_any_provider."""

    @override_settings(
        AI_PROVIDERS=[
            {"name": "openai", "api_key": "sk-test", "base_url": "https://x", "model": "gpt-4"},
            {"name": "deepseek", "api_key": "", "base_url": "https://y", "model": "ds-v3"},
        ],
        AI_TIMEOUT=30,
    )
    def test_load_all_providers(self):
        providers = load_providers()
        assert len(providers) == 2

    @override_settings(
        AI_PROVIDERS=[
            {"name": "openai", "api_key": "sk-test", "base_url": "https://x", "model": "gpt-4"},
            {"name": "deepseek", "api_key": "", "base_url": "https://y", "model": "ds-v3"},
        ],
        AI_TIMEOUT=30,
    )
    def test_active_providers_filters_empty_key(self):
        active = get_active_providers()
        assert len(active) == 1
        assert active[0].name == "openai"

    @override_settings(AI_PROVIDERS=[])
    def test_has_any_provider_false(self):
        assert has_any_provider() is False

    @override_settings(
        AI_PROVIDERS=[
            {"name": "openai", "api_key": "sk-test", "base_url": "https://x", "model": "gpt-4"},
        ],
    )
    def test_has_any_provider_true(self):
        assert has_any_provider() is True
