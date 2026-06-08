"""User serializers — create, update, output."""
from rest_framework import serializers


class UserCreateSerializer(serializers.Serializer):
    """创建用户 — 输入契约 v1.0"""

    username = serializers.CharField(max_length=150, min_length=3)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)
    is_active = serializers.BooleanField(default=True)
    role_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )

    class Meta:
        version = 'v1.0'


class UserUpdateSerializer(serializers.Serializer):
    """更新用户 — 输入契约 v1.0（所有字段可选）"""

    username = serializers.CharField(max_length=150, min_length=3, required=False)
    email = serializers.EmailField(required=False)
    is_active = serializers.BooleanField(required=False)
    role_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )

    class Meta:
        version = 'v1.0'


class UserResetPasswordSerializer(serializers.Serializer):
    """重置密码 — 输入契约 v1.0"""

    password = serializers.CharField(min_length=6, write_only=True)

    class Meta:
        version = 'v1.0'


class UserOutputSerializer(serializers.Serializer):
    """用户信息 — 输出契约 v1.0"""

    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    roles = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        version = 'v1.0'

    def get_roles(self, obj) -> list:
        """查询用户角色列表."""
        from apps.rbac.models import UserRole
        user_roles = UserRole.objects.select_related('role').filter(user_id=obj.id)
        return [
            {'id': ur.role_id, 'name': ur.role.name, 'code': ur.role.code}
            for ur in user_roles
        ]
