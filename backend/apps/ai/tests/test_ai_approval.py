"""Test AIApprovalService — two-phase approval workflow."""
import pytest
from django.test import override_settings

from apps.ai.services.ai_approval import AIApprovalService, SUPPORTED_OPERATIONS
from apps.ai.models import AIApproval, AIApprovalLog
from apps.ai.services.ai_errors import AIApprovalError


@pytest.mark.django_db
class TestApprovalSubmit:
    """Agent 提交操作."""

    def test_submit_success(self, root_user):
        svc = AIApprovalService()
        approval = svc.submit_operation(
            agent_id="agent-001",
            operation="create_user",
            params={"username": "newuser", "password": "P@ss1234"},
            reason="测试创建",
            root_user=root_user,
        )
        assert approval.status == "pending"
        assert approval.agent_id == "agent-001"
        assert approval.operation == "create_user"
        # 应有提交日志
        assert AIApprovalLog.objects.filter(approval=approval, action="submit").exists()

    def test_submit_empty_agent_id_raises(self, root_user):
        svc = AIApprovalService()
        with pytest.raises(AIApprovalError) as exc_info:
            svc.submit_operation(
                agent_id="",
                operation="create_user",
                params={},
                reason="",
                root_user=root_user,
            )
        assert exc_info.value.status == 400

    def test_submit_unsupported_operation_raises(self, root_user):
        svc = AIApprovalService()
        with pytest.raises(AIApprovalError) as exc_info:
            svc.submit_operation(
                agent_id="agent-001",
                operation="drop_database",
                params={},
                reason="hacking",
                root_user=root_user,
            )
        assert "不支持的操作类型" in str(exc_info.value.message)
        assert exc_info.value.status == 400

    def test_submit_without_root_user(self, root_user):
        """Agent 自己提交，root_user=None → 使用系统占位用户（需要有 root 用户存在）."""
        svc = AIApprovalService()
        approval = svc.submit_operation(
            agent_id="agent-001",
            operation="create_user",
            params={},
            reason="auto submit",
        )
        assert approval.status == "pending"


@pytest.mark.django_db
class TestApprovalList:
    """审批列表查询."""

    def test_list_approvals(self, root_user):
        svc = AIApprovalService()
        svc.submit_operation(
            agent_id="agent-001", operation="create_user",
            params={}, reason="r1", root_user=root_user,
        )
        result = svc.list_approvals()
        assert result["total"] >= 1

    def test_list_filter_by_status(self, root_user):
        svc = AIApprovalService()
        svc.submit_operation(
            agent_id="agent-001", operation="create_user",
            params={}, reason="r1", root_user=root_user,
        )
        result = svc.list_approvals(status_filter="pending")
        assert all(item.status == "pending" for item in result["items"])

    def test_list_filter_by_agent_id(self, root_user):
        svc = AIApprovalService()
        svc.submit_operation(
            agent_id="agent-007", operation="create_user",
            params={}, reason="r1", root_user=root_user,
        )
        result = svc.list_approvals(agent_id="agent-007")
        assert all(item.agent_id == "agent-007" for item in result["items"])


@pytest.mark.django_db
class TestApprovalReview:
    """Root 审批操作."""

    def _create_pending(self, svc, root_user):
        return svc.submit_operation(
            agent_id="agent-001", operation="create_user",
            params={"username": "test_approval_user", "password": "P@ss1234"},
            reason="test", root_user=root_user,
        )

    @override_settings(AI_APPROVAL_AUTO_EXECUTE=False)
    def test_approve_without_auto_execute(self, root_user):
        svc = AIApprovalService()
        approval = self._create_pending(svc, root_user)
        result = svc.review(
            approval_id=approval.id,
            root_user=root_user,
            action="approve",
            comment="同意",
        )
        assert result.status == "approved"

    def test_reject(self, root_user):
        svc = AIApprovalService()
        approval = self._create_pending(svc, root_user)
        result = svc.review(
            approval_id=approval.id,
            root_user=root_user,
            action="reject",
            comment="拒绝",
        )
        assert result.status == "rejected"

    def test_review_nonexistent_raises(self, root_user):
        svc = AIApprovalService()
        with pytest.raises(AIApprovalError) as exc_info:
            svc.review(approval_id=99999, root_user=root_user, action="approve")
        assert exc_info.value.status == 404

    def test_review_already_processed_raises(self, root_user):
        svc = AIApprovalService()
        approval = self._create_pending(svc, root_user)
        svc.review(approval_id=approval.id, root_user=root_user, action="reject")
        # 二次审批
        with pytest.raises(AIApprovalError) as exc_info:
            svc.review(approval_id=approval.id, root_user=root_user, action="approve")
        assert "已处理" in str(exc_info.value.message)
        assert exc_info.value.status == 409

    def test_invalid_action_raises(self, root_user):
        svc = AIApprovalService()
        approval = self._create_pending(svc, root_user)
        with pytest.raises(AIApprovalError):
            svc.review(approval_id=approval.id, root_user=root_user, action="maybe")


@pytest.mark.django_db
class TestApprovalGetDetail:
    """审批详情查询."""

    def test_get_detail_exists(self, root_user):
        svc = AIApprovalService()
        approval = svc.submit_operation(
            agent_id="agent-001", operation="create_user",
            params={}, reason="test", root_user=root_user,
        )
        result = svc.get_detail(approval.id)
        assert result.id == approval.id

    def test_get_detail_not_found(self):
        svc = AIApprovalService()
        with pytest.raises(AIApprovalError) as exc_info:
            svc.get_detail(99999)
        assert exc_info.value.status == 404


@pytest.mark.django_db
class TestSupportedOperations:
    """SUPPORTED_OPERATIONS 白名单."""

    def test_supported_ops_keys(self):
        assert "create_user" in SUPPORTED_OPERATIONS
        assert "update_user" in SUPPORTED_OPERATIONS
        assert "delete_user" in SUPPORTED_OPERATIONS
        assert "assign_roles" in SUPPORTED_OPERATIONS

    def test_no_dangerous_ops(self):
        assert "drop_database" not in SUPPORTED_OPERATIONS
        assert "rm_rf" not in SUPPORTED_OPERATIONS
