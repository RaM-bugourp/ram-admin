"""Role serializers — create, update, output."""
from rest_framework import serializers


class RoleCreateSerializer(serializers.Serializer):
    """创建角色 — 输入契约 v1.0"""

    name = serializers.CharField(max_length=100, min_length=2)
    code = serializers.CharField(max_length=50, min_length=2)
    description = serializers.CharField(default='', allow_blank=True)
    is_unique = serializers.BooleanField(default=False)

    class Meta:
        version = 'v1.0'

    def validate_code(self, value):
        import re
        if not re.match(r'^[a-z][a-z0-9_]*$', value):
            raise serializers.ValidationError('角色编码只能包含小写字母、数字和下划线，且以字母开头')
        return value


class RoleUpdateSerializer(serializers.Serializer):
    """更新角色 — 输入契约 v1.0（全可选）"""

    name = serializers.CharField(max_length=100, min_length=2, required=False)
    code = serializers.CharField(max_length=50, min_length=2, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_unique = serializers.BooleanField(required=False)

    class Meta:
        version = 'v1.0'


class RoleOutputSerializer(serializers.Serializer):
    """角色信息 — 输出契约 v1.0"""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    code = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_unique = serializers.BooleanField(read_only=True)
    user_count = serializers.IntegerField(read_only=True, default=0)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        version = 'v1.0'
