"""
User 应用 — 用户模型 + 认证接口
══════════════════════════════════════════════════════════════════

包含：
  - 自定义 User 模型（继承 AbstractUser + 增加 organization）
  - 登录 / 登出 / 获取用户信息 API
  - 序列化器（登录序列化器 + 用户信息序列化器）
  - 视图集（认证相关操作）
"""

from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.user'
    verbose_name = '用户管理'
