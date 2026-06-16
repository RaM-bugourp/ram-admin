"""Test AgentTokenService — HMAC token issue/verify/expire/tamper."""
import time

import pytest
from django.test import override_settings

from apps.ai.permissions import AgentTokenService


class TestAgentTokenIssue:
    """Token 签发."""

    @override_settings(AI_AGENT_TOKEN_SECRET="test-secret-key")
    def test_issue_returns_token_string(self):
        token = AgentTokenService.issue(root_user_id=1, agent_id="agent-001")
        assert isinstance(token, str)
        assert token.count(".") == 3  # exp.root_id.agent_id.sig

    @override_settings(AI_AGENT_TOKEN_SECRET="test-secret-key")
    def test_issue_with_custom_ttl(self):
        token = AgentTokenService.issue(root_user_id=1, agent_id="a1", ttl_hours=1)
        assert isinstance(token, str)


class TestAgentTokenVerify:
    """Token 验证."""

    @override_settings(AI_AGENT_TOKEN_SECRET="test-secret-key")
    def test_verify_valid_token(self):
        token = AgentTokenService.issue(root_user_id=1, agent_id="agent-001")
        payload = AgentTokenService.verify(token)
        assert payload is not None
        assert payload["root_user_id"] == 1
        assert payload["agent_id"] == "agent-001"

    @override_settings(AI_AGENT_TOKEN_SECRET="test-secret-key")
    def test_verify_expired_token(self):
        # 签发一个已过期的 token（ttl=0 → 立刻过期）
        token = AgentTokenService.issue(root_user_id=1, agent_id="a1", ttl_hours=0)
        # ttl_hours=0 → exp = now + 0 → 已过期
        time.sleep(0.1)
        payload = AgentTokenService.verify(token)
        assert payload is None

    @override_settings(AI_AGENT_TOKEN_SECRET="test-secret-key")
    def test_verify_tampered_token(self):
        token = AgentTokenService.issue(root_user_id=1, agent_id="agent-001")
        # 篡改 root_user_id 部分
        parts = token.split(".")
        parts[1] = str(int(parts[1]) + 999)
        tampered = ".".join(parts)
        payload = AgentTokenService.verify(tampered)
        assert payload is None

    @override_settings(AI_AGENT_TOKEN_SECRET="test-secret-key")
    def test_verify_wrong_secret(self):
        token = AgentTokenService.issue(root_user_id=1, agent_id="a1")
        # 换一个 secret 验证
        with override_settings(AI_AGENT_TOKEN_SECRET="wrong-secret"):
            payload = AgentTokenService.verify(token)
        assert payload is None

    def test_verify_empty_token(self):
        assert AgentTokenService.verify("") is None

    def test_verify_malformed_token(self):
        assert AgentTokenService.verify("not.a.valid.token.extra") is None
        assert AgentTokenService.verify("only-two") is None

    def test_verify_non_numeric_exp(self):
        # 手动构造 exp 不是数字的 token
        token = "abc.1.agent.0000deadbeef"
        payload = AgentTokenService.verify(token)
        assert payload is None


class TestAgentTokenRoundTrip:
    """签发→验证 往返."""

    @override_settings(AI_AGENT_TOKEN_SECRET="round-trip-key")
    def test_issue_and_verify_round_trip(self):
        token = AgentTokenService.issue(root_user_id=42, agent_id="agent-42", ttl_hours=24)
        payload = AgentTokenService.verify(token)
        assert payload["root_user_id"] == 42
        assert payload["agent_id"] == "agent-42"
        assert payload["exp"] > int(time.time())

    @override_settings(AI_AGENT_TOKEN_SECRET="round-trip-key")
    def test_different_agents_different_tokens(self):
        t1 = AgentTokenService.issue(root_user_id=1, agent_id="a1")
        t2 = AgentTokenService.issue(root_user_id=1, agent_id="a2")
        p1 = AgentTokenService.verify(t1)
        p2 = AgentTokenService.verify(t2)
        assert p1["agent_id"] != p2["agent_id"]
