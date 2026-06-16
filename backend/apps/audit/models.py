"""Audit log model — login, CRUD, and user operation tracking."""
from django.db import models

from apps.common.base_model import BaseModel
from apps.common.managers import BaseManager


class AuditLog(BaseModel):
    """Operation audit log — every login, CRUD, and important action."""

    ACTION_CHOICES = [
        ('LOGIN',        '登录'),
        ('LOGOUT',       '登出'),
        ('LOGIN_FAIL',   '登录失败'),
        ('CREATE',       '创建'),
        ('UPDATE',       '更新'),
        ('DELETE',       '删除'),
        ('EXPORT',       '导出'),
        ('APPROVE',      '审批'),
        ('REJECT',       '拒绝'),
        ('PASSWORD_RESET', '重置密码'),
        ('ASSIGN_ROLE',  '分配角色'),
        ('OTHER',        '其他'),
    ]

    RESOURCE_CHOICES = [
        ('auth',         '认证'),
        ('user',         '用户'),
        ('role',         '角色'),
        ('dashboard',    '仪表盘'),
        ('ai_chat',      'AI对话'),
        ('ai_approval',  'AI审批'),
        ('ai_audit',     'AI审计'),
        ('other',        '其他'),
    ]

    user = models.ForeignKey(
        'rbac.User', null=True, blank=True,
        on_delete=models.SET_NULL, db_index=True, verbose_name='操作人',
    )
    username = models.CharField(max_length=150, db_index=True, verbose_name='操作人姓名')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, db_index=True, verbose_name='操作类型')
    resource = models.CharField(max_length=30, choices=RESOURCE_CHOICES, db_index=True, verbose_name='资源')
    resource_id = models.CharField(max_length=50, null=True, blank=True, verbose_name='资源ID')
    detail = models.TextField(default='', blank=True, verbose_name='操作详情')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.TextField(default='', blank=True, verbose_name='User-Agent')
    extra_data = models.JSONField(default=dict, blank=True, verbose_name='额外数据')

    objects = BaseManager()

    class Meta:
        db_table = 'audit_logs'
        verbose_name = '审计日志'
        verbose_name_plural = '审计日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at'], name='idx_audit_created'),
            models.Index(fields=['action', 'resource'], name='idx_audit_action_resource'),
        ]

    def __str__(self):
        return f'[{self.action}] {self.username} → {self.resource} @ {self.created_at:%m-%d %H:%M}'
