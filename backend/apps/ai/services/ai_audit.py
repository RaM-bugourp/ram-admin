"""AI audit service — full audit trail for all AI calls and approvals."""
import logging
import uuid

from apps.ai.models import AICallLog, AIApprovalLog
from apps.ai.services.data_formatter import truncate_response

logger = logging.getLogger(__name__)


class AIAuditService:
    """记录所有 AI 调用及审批操作的完整审计链."""

    @staticmethod
    def log_call(
        *,
        root_user=None,
        agent_id: str = '',
        call_type: str,
        prompt: str,
        response: str,
        provider: str,
        failover_triggered: bool = False,
        call_id=None,
        ip_address: str = '',
    ) -> AICallLog:
        """记录一次 AI 调用."""
        return AICallLog.objects.create(
            call_id=call_id or uuid.uuid4(),
            root_user=root_user,
            agent_id=agent_id or '',
            call_type=call_type,
            prompt=(prompt or '')[:2000],
            response=truncate_response(response or '', 5000),
            provider_used=provider or '',
            failover_triggered=failover_triggered,
            ip_address=ip_address or None,
        )

    @staticmethod
    def log_agent_submission(*, agent_id: str, operation: str,
                             params: dict, approval_id) -> AICallLog:
        """Agent 提交审批时记录."""
        import json
        return AICallLog.objects.create(
            call_id=uuid.uuid4(),
            agent_id=agent_id,
            call_type='agent_submission',
            prompt=f"{operation}: {json.dumps(params, ensure_ascii=False)[:1500]}",
            response=f"approval_id={approval_id}",
        )

    @staticmethod
    def log_approval_action(*, approval, root_user, action: str,
                            comment: str = '', ip_address: str = '') -> AIApprovalLog:
        """记录 root 的审批动作（已经在 AIApprovalService.review 内部调用，
        这里保留作为对外接口便于扩展）."""
        return AIApprovalLog.objects.create(
            approval=approval,
            root_user=root_user,
            action=action,
            comment=comment or '',
            ip_address=ip_address or None,
        )

    # ── 查询 ────────────────────────────────────────────────────

    @staticmethod
    def query_calls(
        *,
        start_date=None,
        end_date=None,
        call_type: str = '',
        root_user_id: int | None = None,
        agent_id: str = '',
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        from django.core.paginator import Paginator
        qs = AICallLog.objects.all().order_by('-created_at')
        if start_date:
            qs = qs.filter(created_at__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__lte=end_date)
        if call_type:
            qs = qs.filter(call_type=call_type)
        if root_user_id:
            qs = qs.filter(root_user_id=root_user_id)
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

    @staticmethod
    def cleanup_old_logs(retention_days: int = 90) -> int:
        """删除超过保留期的审计日志，返回删除条数."""
        if not retention_days or retention_days <= 0:
            return 0
        from datetime import timedelta
        from django.utils import timezone
        cutoff = timezone.now() - timedelta(days=retention_days)
        deleted, _ = AICallLog.objects.filter(created_at__lt=cutoff).delete()
        logger.info("Cleaned up %d old AICallLog records", deleted)
        return deleted
