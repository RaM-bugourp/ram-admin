"""AI models — call log, approval workflow, approval log, in-app notification."""
import uuid

from django.db import models

from apps.common.base_model import BaseModel
from apps.common.managers import BaseManager


# ── 调用日志 ────────────────────────────────────────────────────────

class AICallLog(BaseModel):
    """AI 调用日志 — 记录谁在什么时候调用了什么.

    两种来源：
      - root 直接调用 → root_user=<user>, agent_id=None
      - Agent 代发    → root_user=None,  agent_id=<id>
    """

    call_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="调用ID")
    root_user = models.ForeignKey(
        'rbac.User', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='ai_calls', verbose_name="调用用户",
    )
    agent_id = models.CharField(max_length=100, blank=True, default='', verbose_name="Agent ID")
    call_type = models.CharField(max_length=50, verbose_name="调用类型")
    # chat | analyze | report | agent_submission
    prompt = models.TextField(blank=True, default='', verbose_name="输入")
    response = models.TextField(blank=True, default='', verbose_name="响应")
    provider_used = models.CharField(max_length=50, blank=True, default='', verbose_name="使用的Provider")
    failover_triggered = models.BooleanField(default=False, verbose_name="是否故障转移")
    tokens_used = models.IntegerField(null=True, blank=True, verbose_name="Token用量")
    cost = models.DecimalField(
        max_digits=12, decimal_places=6, null=True, blank=True, verbose_name="费用"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP地址")

    objects = BaseManager()

    class Meta:
        db_table = 'ai_call_logs'
        verbose_name = 'AI调用日志'
        verbose_name_plural = 'AI调用日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['root_user'], name='idx_aicall_root'),
            models.Index(fields=['agent_id'], name='idx_aicall_agent'),
            models.Index(fields=['call_type'], name='idx_aicall_type'),
        ]

    def __str__(self):
        who = self.root_user.username if self.root_user else (self.agent_id or 'anon')
        return f"[{self.call_type}] {who} @ {self.created_at:%Y-%m-%d %H:%M}"


# ── Agent 审批流 ────────────────────────────────────────────────────

APPROVAL_STATUS_CHOICES = [
    ('pending', '待审批'),
    ('approved', '已通过'),
    ('rejected', '已拒绝'),
    ('timeout', '已超时'),
    ('executed', '已执行'),
    ('failed', '执行失败'),
]


class AIApproval(BaseModel):
    """Agent 操作审批记录.

    两阶段审批：
      1. Agent submit_operation → status=pending
      2. Root review → approve (执行) / reject
    """

    approval_uid = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, verbose_name="审批ID"
    )
    agent_id = models.CharField(max_length=100, verbose_name="Agent ID")
    operation = models.CharField(max_length=100, verbose_name="操作类型")
    # create_user | update_user | delete_user | assign_roles | ...
    params = models.JSONField(default=dict, blank=True, verbose_name="操作参数")
    reason = models.TextField(blank=True, default='', verbose_name="提交原因")
    status = models.CharField(
        max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending', verbose_name="状态"
    )
    submitted_by = models.ForeignKey(
        'rbac.User', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='submitted_ai_approvals', verbose_name='真实提交主体（历史可未知）',
    )
    approved_by = models.ForeignKey(
        'rbac.User', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='ai_approvals', verbose_name="审批人",
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="审批时间")
    approver_comment = models.TextField(blank=True, default='', verbose_name="审批备注")
    executed_at = models.DateTimeField(null=True, blank=True, verbose_name="执行时间")
    execution_error = models.TextField(blank=True, default='', verbose_name="执行错误")

    objects = BaseManager()

    class Meta:
        db_table = 'ai_approvals'
        verbose_name = 'AI审批'
        verbose_name_plural = 'AI审批'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status'], name='idx_aiappr_status'),
            models.Index(fields=['agent_id'], name='idx_aiappr_agent'),
        ]

    def __str__(self):
        return f"{self.agent_id}:{self.operation} [{self.status}]"


class AIApprovalLog(BaseModel):
    """审批操作日志 — 记录 root 的每一次审批动作."""

    approval = models.ForeignKey(
        AIApproval, on_delete=models.CASCADE, related_name='logs', verbose_name="审批记录"
    )
    root_user = models.ForeignKey(
        'rbac.User', on_delete=models.CASCADE, related_name='ai_approval_logs', verbose_name="审批人"
    )
    action = models.CharField(max_length=20, verbose_name="动作")
    # approve | reject | submit | execute
    comment = models.TextField(blank=True, default='', verbose_name="备注")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP地址")

    objects = BaseManager()

    class Meta:
        db_table = 'ai_approval_logs'
        verbose_name = 'AI审批日志'
        verbose_name_plural = 'AI审批日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.approval_id}:{self.action}"


# ── 站内通知（Provider 告警用）──────────────────────────────────────

NOTIFICATION_LEVEL_CHOICES = [
    ('info', '信息'),
    ('success', '成功'),
    ('warning', '警告'),
    ('error', '错误'),
]


class Notification(BaseModel):
    """站内通知 — 当前主要用于 AI Provider 故障告警."""

    recipient = models.ForeignKey(
        'rbac.User', on_delete=models.CASCADE, related_name='ai_notifications',
        verbose_name="接收人",
    )
    title = models.CharField(max_length=200, verbose_name="标题")
    message = models.TextField(verbose_name="内容")
    level = models.CharField(
        max_length=20, choices=NOTIFICATION_LEVEL_CHOICES, default='info', verbose_name="级别"
    )
    is_read = models.BooleanField(default=False, verbose_name="已读")

    objects = BaseManager()

    class Meta:
        db_table = 'ai_notifications'
        verbose_name = 'AI通知'
        verbose_name_plural = 'AI通知'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read'], name='idx_ainote_unread'),
        ]

    def __str__(self):
        return f"[{self.level}] {self.title} → {self.recipient_id}"

    def mark_read(self):
        self.is_read = True
        self.save(update_fields=['is_read', 'updated_at'])


class AgentCredential(models.Model):
    """Revocable v2 credential registry. No raw token or signing secret is stored.

    Intentionally not BaseModel: revocation has no soft-delete/filter bypass.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_digest = models.CharField(max_length=64, unique=True, editable=False)
    issuer = models.ForeignKey('rbac.User', on_delete=models.CASCADE, related_name='agent_credentials')
    agent_id = models.CharField(max_length=100)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ai_agent_credentials'

