"""
操作日志模型
══════════════════════════════════════════════════════════════════

OperationLog：记录所有 API 操作（谁、什么时间、做了什么、结果如何）

为什么需要操作日志？
    —— 合规要求：金融、医疗等行业的审计需求
    —— 问题排查：线上出问题可以回溯操作记录
    —— 安全监控：谁在什么时间删了数据？

设计思路：
    —— 中间件自动记录，不需要每个视图手动调用
    —— 不记录 GET 列表请求（太频繁，且价值低）
    —— 敏感字段（密码、Token）自动过滤
    —— 支持 ContentType 关联，可追溯操作对象
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType


class OperationLog(models.Model):
    """
    操作日志模型。

    记录内容：
        —— 操作人（user/username）
        —— 操作类型（view/create/update/delete/list）
        —— 操作对象（content_type + object_id，通用外键）
        —— 请求信息（URL、方法、参数、IP、UA）
        —— 响应信息（状态码、错误信息）
        —— 时间戳

    GenericForeignKey 是什么？
        —— Django 的「内容类型框架」允许你关联任意模型
        —— 不需要提前知道要关联哪个模型
        —— 原理：存 app_label + model + pk 三个字段
    """

    ACTION_CHOICES = (
        ('VIEW', '访问'),
        ('LIST', '列表'),
        ('CREATE', '新增'),
        ('UPDATE', '更新'),
        ('DELETE', '删除'),
        ('OTHER', '其他'),
    )

    # 操作人
    user = models.ForeignKey(
        'rbac.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='operation_logs',
        verbose_name='操作用户'
    )
    username = models.CharField(max_length=128, blank=True, default='', verbose_name='用户名（冗余存储）')

    # 操作类型
    action_type = models.CharField(max_length=16, choices=ACTION_CHOICES, default='OTHER', verbose_name='操作类型')

    # GenericForeignKey：关联被操作的对象
    # content_type：记录是哪个 app 的哪个 model（如 rbac.User）
    # object_id：记录该条数据的 pk（如 42）
    # object_repr：记录操作对象的字符串表示（如 "admin用户"）
    content_type = models.ForeignKey(
        ContentType, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='operation_logs'
    )
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='对象ID')
    object_repr = models.CharField(max_length=255, blank=True, default='', verbose_name='对象描述')

    # 请求信息
    request_path = models.CharField(max_length=512, verbose_name='请求路径')
    request_method = models.CharField(max_length=10, verbose_name='请求方法')
    request_params = models.JSONField(default=dict, verbose_name='请求参数')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.CharField(max_length=500, blank=True, default='', verbose_name='User-Agent')

    # 响应信息
    status_code = models.PositiveIntegerField(default=0, verbose_name='状态码')
    error_message = models.CharField(max_length=1000, blank=True, default='', verbose_name='错误信息')

    # 时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        verbose_name = '操作日志'
        verbose_name_plural = '操作日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['username']),
            models.Index(fields=['action_type']),
            models.Index(fields=['request_path']),
        ]

    def __str__(self):
        return f"{self.username} {self.get_action_type_display()} {self.request_path}"

    @property
    def content_object(self):
        """GenericForeignKey 的反向访问属性"""
        if self.content_type and self.object_id:
            return self.content_type.get_object_for_this_type(pk=self.object_id)
        return None
