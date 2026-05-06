"""
User 序列化器
"""

from rest_framework import serializers
from .models import User


class LoginSerializer(serializers.Serializer):
    """
    登录请求序列化器

    为什么不用 ModelSerializer？
        —— 登录只需要 username + password，不需要完整的 User 模型字段
        —— 而且 password 不应该出现在响应里
    """
    username = serializers.CharField(max_length=150, min_length=2)
    password = serializers.CharField(max_length=128, write_only=True, style={'input_type': 'password'})


class UserInfoSerializer(serializers.ModelSerializer):
    """
    用户信息序列化器（返回给前端的内容）

    注意：不要返回 password！
    """
    role_names = serializers.SerializerMethodField()
    permission_codes = serializers.SerializerMethodField()
    primary_organization_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'avatar',
            'is_superuser', 'is_active',
            'primary_organization_id', 'primary_organization_name',
            'role_names', 'permission_codes',
            'date_joined', 'last_login',
        ]
        read_only_fields = fields

    def get_role_names(self, obj):
        return obj.get_role_names()

    def get_permission_codes(self, obj):
        return obj.get_permission_codes()

    def get_primary_organization_name(self, obj):
        org = obj.get_primary_organization()
        return org.name if org else ''


class UserListSerializer(serializers.ModelSerializer):
    """用户列表序列化器（管理员用，少字段）"""
    primary_organization_name = serializers.SerializerMethodField()
    role_names = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone',
            'is_superuser', 'is_active',
            'primary_organization_id', 'primary_organization_name', 'role_names',
            'date_joined', 'last_login',
        ]

    def get_role_names(self, obj):
        return obj.get_role_names()

    def get_primary_organization_name(self, obj):
        org = obj.get_primary_organization()
        return org.name if org else ''
