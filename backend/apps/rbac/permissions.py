"""RBAC permissions — role-based access control."""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    只有 root 或 boss 角色可以执行写操作，普通用户只读.

    检查优先级:
        1. is_superuser → 放行
        2. 持有 root 角色 → 放行
        3. 持有 boss 角色 → 放行
        4. SAFE_METHODS (GET/HEAD/OPTIONS) → 放行（任何已认证用户）
        5. 其他 → 拒绝 (403)
    """

    message = '仅超级管理员或 BOSS 角色可执行此操作'

    ADMIN_ROLES = {'root', 'boss'}

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Superuser 直接放行
        if user.is_superuser:
            return True

        # 读操作放行
        if request.method in SAFE_METHODS:
            return True

        # 检查角色：root 或 boss
        return self._has_admin_role(user)

    def _has_admin_role(self, user) -> bool:
        """检查用户是否持有 root 或 boss 角色."""
        if not user.id:
            return False
        from apps.rbac.models import UserRole
        return UserRole.objects.filter(
            user=user,
            role__code__in=self.ADMIN_ROLES,
        ).exists()
