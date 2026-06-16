"""Test AI models — AICallLog, AIApproval, Notification creation + status choices."""
import pytest

from apps.ai.models import (
    AICallLog,
    AIApproval,
    AIApprovalLog,
    Notification,
    APPROVAL_STATUS_CHOICES,
    NOTIFICATION_LEVEL_CHOICES,
)


@pytest.mark.django_db
class TestAICallLog:
    """AI 调用日志模型."""

    def test_create_call_log(self, root_user):
        log = AICallLog.objects.create(
            root_user=root_user,
            call_type="chat",
            prompt="你好",
            response="你好！",
            provider_used="mock",
        )
        assert log.pk is not None
        assert log.call_type == "chat"
        assert log.provider_used == "mock"

    def test_call_log_str(self, root_user):
        log = AICallLog.objects.create(
            root_user=root_user,
            call_type="chat",
            prompt="hi",
            response="hello",
        )
        s = str(log)
        assert "chat" in s

    def test_call_log_agent(self):
        log = AICallLog.objects.create(
            agent_id="agent-001",
            call_type="agent_submission",
            prompt="create user",
        )
        assert log.root_user is None
        assert log.agent_id == "agent-001"

    def test_call_log_optional_fields(self, root_user):
        log = AICallLog.objects.create(
            root_user=root_user,
            call_type="analyze",
        )
        assert log.tokens_used is None
        assert log.cost is None
        assert log.ip_address is None


@pytest.mark.django_db
class TestAIApproval:
    """AI 审批模型."""

    def test_create_approval(self):
        approval = AIApproval.objects.create(
            agent_id="agent-001",
            operation="create_user",
            params={"username": "test"},
            reason="自动创建",
            status="pending",
        )
        assert approval.pk is not None
        assert approval.status == "pending"
        assert approval.approval_uid is not None

    def test_approval_str(self):
        approval = AIApproval.objects.create(
            agent_id="agent-001",
            operation="delete_user",
            status="pending",
        )
        s = str(approval)
        assert "agent-001" in s
        assert "delete_user" in s

    def test_approval_status_choices(self):
        codes = [c[0] for c in APPROVAL_STATUS_CHOICES]
        assert "pending" in codes
        assert "approved" in codes
        assert "rejected" in codes
        assert "executed" in codes
        assert "failed" in codes

    def test_approval_default_params(self):
        approval = AIApproval.objects.create(
            agent_id="agent-001",
            operation="create_user",
        )
        assert approval.params == {}


@pytest.mark.django_db
class TestAIApprovalLog:
    """审批操作日志模型."""

    def test_create_approval_log(self, root_user):
        approval = AIApproval.objects.create(
            agent_id="agent-001", operation="create_user", status="pending"
        )
        log = AIApprovalLog.objects.create(
            approval=approval,
            root_user=root_user,
            action="submit",
            comment="Agent 提交",
        )
        assert log.pk is not None
        assert log.action == "submit"

    def test_approval_log_str(self, root_user):
        approval = AIApproval.objects.create(
            agent_id="agent-001", operation="create_user", status="pending"
        )
        log = AIApprovalLog.objects.create(
            approval=approval, root_user=root_user, action="approve"
        )
        s = str(log)
        assert "approve" in s


@pytest.mark.django_db
class TestNotification:
    """站内通知模型."""

    def test_create_notification(self, root_user):
        n = Notification.objects.create(
            recipient=root_user,
            title="Provider 告警",
            message="openai 连续失败 3 次",
            level="warning",
        )
        assert n.pk is not None
        assert n.is_read is False

    def test_mark_read(self, root_user):
        n = Notification.objects.create(
            recipient=root_user,
            title="test",
            message="msg",
        )
        assert n.is_read is False
        n.mark_read()
        n.refresh_from_db()
        assert n.is_read is True

    def test_notification_level_choices(self):
        codes = [c[0] for c in NOTIFICATION_LEVEL_CHOICES]
        assert "info" in codes
        assert "warning" in codes
        assert "error" in codes

    def test_notification_str(self, root_user):
        n = Notification.objects.create(
            recipient=root_user,
            title="告警",
            message="msg",
            level="error",
        )
        s = str(n)
        assert "error" in s
