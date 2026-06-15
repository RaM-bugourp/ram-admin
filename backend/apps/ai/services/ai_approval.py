"""AI approval workflow — two-phase approval for Agent write operations."""
import logging
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.ai.models import AIApproval, AIApprovalLog
from apps.ai.services.ai_errors import AIApprovalError
from apps.common.exceptions import BusinessError

logger = logging.getLogger(__name__)


class AIApprovalService:
    """Agent 操作两阶段审批.

    1. Agent 提交操作 → status=pending
    2. Root 审批：
       - approve → status=approved → 自动执行 → status=executed
       - reject  → status=rejected
    """

    # ── 提交 ────────────────────────────────────────────────────

    @transaction.atomic
    def submit_operation(
        self, *, agent_id: str, operation: str,
        params: dict, reason: str, root_user=None,
    ) -> AIApproval:
        """Agent 提交操作（Agent 自身不能执行写操作）."""
        if not agent_id:
            raise AIApprovalError('agent_id 不能为空', status=400)
        if operation not in SUPPORTED_OPERATIONS:
            raise AIApprovalError(
                f'不支持的操作类型: {operation}（支持: {", ".join(SUPPORTED_OPERATIONS)}）',
                status=400,
            )

        approval = AIApproval.objects.create(
            agent_id=agent_id,
            operation=operation,
            params=params or {},
            reason=reason or '',
            status='pending',
        )

        # 审计：提交动作
        if root_user is not None:
            AIApprovalLog.objects.create(
                approval=approval, root_user=root_user,
                action='submit', comment=reason or '',
            )
        else:
            AIApprovalLog.objects.create(
                approval=approval, root_user_id=_system_user_id(),
                action='submit', comment=f"agent={agent_id}: {reason or ''}",
            )

        logger.info("AI approval submitted: agent=%s op=%s id=%s",
                    agent_id, operation, approval.id)
        return approval

    # ── 列表查询 ────────────────────────────────────────────────

    def list_approvals(self, *, status_filter: str = '',
                       agent_id: str = '', page: int = 1, page_size: int = 20) -> dict:
        from django.core.paginator import Paginator
        qs = AIApproval.objects.all().order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if agent_id:
            qs = qs.filter(agent_id=agent_id)

        paginator = Paginator(qs, min(page_size, 100))
        page_obj = paginator.get_page(page)
        return {
            'items': list(page_obj.object_list),
            'page': page_obj.number,
            'page_size': min(page_size, 100),
            'total': paginator.count,
            'total_pages': paginator.num_pages,
        }

    def get_detail(self, approval_id: int) -> AIApproval:
        try:
            return AIApproval.objects.get(id=approval_id)
        except AIApproval.DoesNotExist:
            raise AIApprovalError('审批记录不存在', code='APPROVAL_NOT_FOUND', status=404)

    # ── 审批 ────────────────────────────────────────────────────

    @transaction.atomic
    def review(self, *, approval_id: int, root_user, action: str,
               comment: str = '', ip_address: str = '') -> AIApproval:
        """Root 用户审批操作."""
        if action not in ('approve', 'reject'):
            raise AIApprovalError('action 必须是 approve 或 reject', status=400)

        try:
            approval = AIApproval.objects.get(id=approval_id)
        except AIApproval.DoesNotExist:
            raise AIApprovalError('审批记录不存在', code='APPROVAL_NOT_FOUND', status=404)

        if approval.status != 'pending':
            raise AIApprovalError(
                f'该审批已处理 (当前状态: {approval.status})',
                code='APPROVAL_ALREADY_PROCESSED', status=409,
            )

        approval.approved_by = root_user
        approval.approved_at = timezone.now()
        approval.approver_comment = comment or ''

        if action == 'reject':
            approval.status = 'rejected'
            approval.save()
            AIApprovalLog.objects.create(
                approval=approval, root_user=root_user,
                action='reject', comment=comment or '', ip_address=ip_address or None,
            )
            logger.info("AI approval #%s REJECTED by %s", approval_id, root_user.username)
            return approval

        # approve
        approval.status = 'approved'
        approval.save()
        AIApprovalLog.objects.create(
            approval=approval, root_user=root_user,
            action='approve', comment=comment or '', ip_address=ip_address or None,
        )

        # 自动执行（如果配置开启）
        if getattr(__import__('django.conf', fromlist=['settings']).settings,
                   'AI_APPROVAL_AUTO_EXECUTE', True):
            try:
                self._execute_operation(approval)
                approval.status = 'executed'
                approval.executed_at = timezone.now()
                approval.save()
                AIApprovalLog.objects.create(
                    approval=approval, root_user=root_user, action='execute',
                    comment='自动执行成功',
                )
                logger.info("AI approval #%s EXECUTED", approval_id)
            except Exception as e:  # noqa: BLE001 — 执行失败要落库
                approval.status = 'failed'
                approval.execution_error = str(e)[:1000]
                approval.save()
                AIApprovalLog.objects.create(
                    approval=approval, root_user=root_user, action='execute',
                    comment=f'执行失败: {e}',
                )
                logger.exception("AI approval #%s execution FAILED: %s", approval_id, e)

        return approval

    # ── 操作执行分发 ────────────────────────────────────────────

    def _execute_operation(self, approval: AIApproval) -> None:
        """根据 operation 类型分发到对应 Service."""
        handler = SUPPORTED_OPERATIONS.get(approval.operation)
        if not handler:
            raise AIApprovalError(f'不支持的操作: {approval.operation}', status=400)
        handler(approval.params)


# ── 支持的操作集（白名单）─────────────────────────────────────

def _op_create_user(params: dict) -> dict:
    from apps.rbac.services.user_service import UserService
    user = UserService().create_user(params)
    return {'user_id': user.id, 'username': user.username}


def _op_update_user(params: dict) -> dict:
    from apps.rbac.services.user_service import UserService
    user_id = params.get('user_id') or params.get('id')
    if not user_id:
        raise AIApprovalError('update_user 需要 user_id', status=400)
    data = {k: v for k, v in params.items() if k not in ('user_id', 'id')}
    user = UserService().update_user(int(user_id), data)
    return {'user_id': user.id}


def _op_delete_user(params: dict) -> dict:
    from apps.rbac.services.user_service import UserService
    user_id = params.get('user_id') or params.get('id')
    if not user_id:
        raise AIApprovalError('delete_user 需要 user_id', status=400)
    UserService().delete_user(int(user_id))
    return {'deleted': True}


def _op_assign_roles(params: dict) -> dict:
    from apps.rbac.services.user_service import UserService
    user_id = params.get('user_id')
    role_ids = params.get('role_ids', [])
    if not user_id:
        raise AIApprovalError('assign_roles 需要 user_id', status=400)
    UserService().update_user(int(user_id), {'role_ids': role_ids})
    return {'user_id': user_id, 'role_ids': role_ids}


SUPPORTED_OPERATIONS = {
    'create_user': _op_create_user,
    'update_user': _op_update_user,
    'delete_user': _op_delete_user,
    'assign_roles': _op_assign_roles,
}


def _system_user_id() -> int:
    """获取一个系统占位用户 ID（用于 Agent 提交时无 root 的审计落库）.

    优先用第一个 root 用户，找不到则用第一个用户，都没有则 0。
    """
    from apps.rbac.models import User, UserRole
    root = UserRole.objects.filter(role__code='root').order_by('user_id').first()
    if root:
        return root.user_id
    any_user = User.objects.first()
    return any_user.id if any_user else 0
