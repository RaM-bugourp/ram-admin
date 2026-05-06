"""
RBAC 权限系统 —— 统一导出

使用示例：

    # 1. 权限类（声明式，用于 settings.py 全局配置）
    from ram_core.permissions import RBACPermission

    REST_FRAMEWORK = {
        'DEFAULT_PERMISSION_CLASSES': [
            'ram_core.permissions.RBACPermission',
        ],
    }

    # 2. 基于权限码的精确权限（ViewSet 内使用）
    from ram_core.permissions import RBACPermissionByCode

    class ArticleViewSet(RBACPermissionByCode, ModelViewSet):
        permission_code_map = {
            'list': 'article:list',
            'create': 'article:create',
            'update': 'article:update',
            'destroy': 'article:delete',
        }

    # 3. 数据权限过滤
    from ram_core.permissions import DataScopeFilter

    class ArticleViewSet(DataScopeFilter, ModelViewSet):
        ...

    # 4. 模型导入
    from ram_core.permissions.models import (
        Menu, Permission, Role, UserRole,
        Organization, UserOrganization,
    )
"""

from .models import (
    Menu,
    Permission,
    Role,
    UserRole,
    Organization,
    UserOrganization,
)
from .views import (
    RBACPermission,
    RBACPermissionByCode,
    rbac_permission,
    DataScopeFilter,
)

__all__ = [
    # models
    'Menu', 'Permission', 'Role', 'UserRole',
    'Organization', 'UserOrganization',
    # permissions
    'RBACPermission',
    'RBACPermissionByCode',
    'rbac_permission',
    'DataScopeFilter',
]
