"""
User 模型 — 自定义用户模型
══════════════════════════════════════════════════════════════════

注意：Organization 的导入放在类定义外面，避免循环依赖。
apps/rbac/models.py 需要先加载完，Organization 才能被正确引用。
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    自定义用户模型 —— 继承 AbstractUser，扩展组织归属字段。

    注意：必须在 settings.py 里设置 AUTH_USER_MODEL = 'apps.user.User'
    且在 migrate 之前就定义好（否则需要清空数据库重建）。
    """

    phone = models.CharField(
        '手机号', max_length=11, blank=True, default='',
        help_text='用于接收通知，11位手机号'
    )
    avatar = models.URLField(
        '头像URL', blank=True, default='',
        help_text='头像图片地址'
    )

    # primary_organization 在这里不定义外键
    # 而是在 UserOrganization 里通过 FK 关联
    primary_organization_id = models.IntegerField(
        '主要归属组织ID', null=True, blank=True,
        help_text='UserOrganization 的 ID，通过外键关联'
    )

    class Meta:
        db_table = 'sys_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

    @property
    def is_super_admin(self):
        """是否是超级管理员"""
        return self.is_superuser

    def get_role_names(self):
        """获取用户所有角色名"""
        return list(self.roles.values_list('name', flat=True))

    def get_permission_codes(self):
        """获取用户所有权限码列表（扁平化）"""
        codes = set()
        for role in self.roles.all():
            for perm in role.permissions.all():
                codes.add(perm.code)
        return list(codes)

    def get_primary_organization(self):
        """获取主要归属组织（延迟导入避免循环）"""
        if not self.primary_organization_id:
            return None
        from apps.rbac.models import Organization
        try:
            return Organization.objects.get(pk=self.primary_organization_id)
        except Organization.DoesNotExist:
            return None

    def get_organization_ids(self):
        """获取用户所在的所有组织 ID"""
        org_ids = set()
        from apps.rbac.models import Organization
        for uo in self.userorganization_set.all():
            org = uo.organization
            ancestor_ids = org.get_ancestors(include_self=True).values_list('id', flat=True)
            org_ids.update(ancestor_ids)
        return list(org_ids)


class UserOrganization(models.Model):
    """
    用户-组织关联表

    注意：organization 使用字符串引用（'Organization'），避免循环导入。
    Django 会在所有模型加载完成后再解析这个引用。
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    organization = models.ForeignKey(
        'rbac.Organization',  # 字符串引用，避免循环导入（app_label = rbac）
        on_delete=models.CASCADE,
        verbose_name='组织',
    )
    is_leader = models.BooleanField('是否负责人', default=False)
    created_at = models.DateTimeField('加入时间', auto_now_add=True)

    class Meta:
        db_table = 'sys_user_organization'
        verbose_name = '用户组织关联'
        verbose_name_plural = verbose_name
        unique_together = ('user', 'organization')
