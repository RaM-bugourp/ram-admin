"""Two-phase optional agent workflow with explicit current human authority."""
from django.db import transaction
from django.utils import timezone
from apps.ai.models import AIApproval,AIApprovalLog
from apps.ai.services.ai_errors import AIApprovalError
from apps.ai.permissions import _has_root_role
from apps.ai.services.approval_params import prepare
from apps.common.exceptions import BusinessError

def require_root(user):
    from apps.rbac.permissions import effective_user
    current=effective_user(user)
    if not _has_root_role(current): raise AIApprovalError('需要有效root',code='PERMISSION_DENIED',status=403)
    return current

class AIApprovalService:
    @transaction.atomic
    def submit_operation(self,*,agent_id,operation,params,reason,root_user=None):
        issuer=require_root(root_user)
        if not agent_id or operation not in SUPPORTED_OPERATIONS: raise AIApprovalError('不支持的操作',status=400)
        params=prepare(operation,params)
        approval=AIApproval.objects.create(agent_id=agent_id,operation=operation,params=params,reason='[REDACTED submission reason]' if reason else '',status='pending',submitted_by=issuer)
        AIApprovalLog.objects.create(approval=approval,root_user=issuer,action='submit',comment='提交审批')
        from apps.ai.services.ai_audit import AIAuditService
        AIAuditService.log_agent_submission(agent_id=agent_id,operation=operation,params={},approval_id=approval.pk,root_user=issuer)
        return approval
    def list_approvals(self,*,status_filter='',agent_id='',page=1,page_size=20):
        from django.core.paginator import Paginator
        qs=AIApproval.objects.order_by('-created_at','-id')
        if status_filter: qs=qs.filter(status=status_filter)
        if agent_id: qs=qs.filter(agent_id=agent_id)
        paginator=Paginator(qs,page_size);obj=paginator.get_page(page)
        return {'items':list(obj.object_list),'page':obj.number,'page_size':page_size,'total':paginator.count,'total_pages':paginator.num_pages}
    def get_detail(self,approval_id):
        try:return AIApproval.objects.get(pk=approval_id)
        except AIApproval.DoesNotExist:raise AIApprovalError('审批记录不存在',code='APPROVAL_NOT_FOUND',status=404)
    @transaction.atomic
    def review(self,*,approval_id,root_user,action,comment='',ip_address=''):
        from apps.rbac.services.locking import reserve_lifecycle_write
        reserve_lifecycle_write()
        reviewer=require_root(root_user)
        if action not in ('approve','reject'):raise AIApprovalError('无效action',status=400)
        approval=AIApproval.objects.select_for_update().filter(pk=approval_id).first()
        if not approval:raise AIApprovalError('审批记录不存在',code='APPROVAL_NOT_FOUND',status=404)
        # Conditional claim also prevents double execution on SQLite where row locks are no-ops.
        state='approved' if action=='approve' else 'rejected'
        now=timezone.now()
        if AIApproval.objects.filter(pk=approval_id,status='pending').update(status=state,approved_by=reviewer,approved_at=now,approver_comment='[REDACTED review comment]' if comment else '')!=1:
            raise AIApprovalError('审批已处理',code='APPROVAL_ALREADY_PROCESSED',status=409)
        approval.refresh_from_db()
        AIApprovalLog.objects.create(approval=approval,root_user=reviewer,action=action,comment='审批通过' if action=='approve' else '审批拒绝',ip_address=ip_address or None)
        from django.conf import settings
        if action=='approve' and getattr(settings,'AI_APPROVAL_AUTO_EXECUTE',True):
            try:
                with transaction.atomic():
                    self._execute_operation(approval,actor=reviewer)
                    approval.status='executed';approval.executed_at=timezone.now()
                    approval.params={k:v for k,v in approval.params.items() if k!='password_digest'}
                    approval.save()
                    AIApprovalLog.objects.create(approval=approval,root_user=reviewer,action='execute',comment='执行成功')
            except Exception as error:
                approval.refresh_from_db();approval.status='failed'
                # Error messages may contain submitted values; store only a bounded code.
                approval.execution_error=getattr(error,'code',None) or type(error).__name__
                approval.params={k:v for k,v in approval.params.items() if k!='password_digest'}
                approval.save()
                AIApprovalLog.objects.create(approval=approval,root_user=reviewer,action='execute',comment='执行失败')
        if action=='reject':
            approval.params={k:v for k,v in approval.params.items() if k!='password_digest'};approval.save(update_fields=['params'])
        return approval
    def _execute_operation(self,approval,*,actor=None):
        actor=require_root(actor)
        from apps.rbac.services.user_service import UserService
        service=UserService();params=dict(approval.params)
        if approval.operation=='create_user': return service.create_from_approval(approval,actor=actor)
        user_id=params.pop('user_id',None)
        if type(user_id) is not int or user_id<=0:raise AIApprovalError('缺少有效user_id',status=400)
        if approval.operation=='delete_user':return service.delete_user(user_id,actor=actor)
        if approval.operation in ('update_user','assign_roles'):return service.update_user(user_id,params,actor=actor)
        raise AIApprovalError('不支持的操作',status=400)

# Public operation names remain stable; no handler may omit an actor.
SUPPORTED_OPERATIONS={name:None for name in ('create_user','update_user','delete_user','assign_roles')}
