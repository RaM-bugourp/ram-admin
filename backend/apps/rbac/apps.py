"""
apps/rbac/apps.py
"""

from django.apps import AppConfig


class RbacConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.rbac'
    verbose_name = '权限管理'

    def ready(self):
        # 注册信号（可选）
        pass
