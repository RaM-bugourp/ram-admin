"""
apps/rbac/serializers.py
"""

from rest_framework import serializers
from .models import Organization, Menu, Permission, Role


class OrganizationSerializer(serializers.ModelSerializer):
    """组织序列化器"""
    parent_name = serializers.CharField(source='parent.name', read_only=True, default='')

    class Meta:
        model = Organization
        fields = ['id', 'name', 'code', 'parent', 'parent_name',
                  'sort', 'is_active', 'created_at', 'updated_at']


class MenuSerializer(serializers.ModelSerializer):
    """菜单序列化器"""
    parent_title = serializers.CharField(source='parent.title', read_only=True, default='')

    class Meta:
        model = Menu
        fields = ['id', 'title', 'name', 'path', 'icon', 'component',
                  'sort', 'is_hidden', 'is_active', 'parent', 'parent_title']


class MenuTreeSerializer(serializers.Serializer):
    """菜单树序列化器（递归结构）"""
    id = serializers.IntegerField()
    title = serializers.CharField()
    name = serializers.CharField(required=False, default='')
    path = serializers.CharField(required=False, default='')
    icon = serializers.CharField(required=False, default='')
    component = serializers.CharField(required=False, default='')
    isHidden = serializers.BooleanField(source='is_hidden', required=False, default=False)
    children = serializers.SerializerMethodField(required=False)

    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by('sort', 'id')
        return MenuTreeSerializer(children, many=True).data


class PermissionSerializer(serializers.ModelSerializer):
    """权限序列化器"""
    menu_title = serializers.CharField(source='menu.title', read_only=True, default='')

    class Meta:
        model = Permission
        fields = ['id', 'name', 'code', 'url_pattern', 'menu', 'menu_title',
                  'ptype', 'is_active', 'description', 'sort']


class RoleSerializer(serializers.ModelSerializer):
    """角色列表序列化器"""
    permission_count = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'description', 'data_scope',
                  'is_active', 'sort', 'permission_count', 'user_count',
                  'created_at', 'updated_at']

    def get_permission_count(self, obj):
        return obj.permissions.count()

    def get_user_count(self, obj):
        return obj.users.count()


class RoleDetailSerializer(RoleSerializer):
    """角色详情序列化器（含关联的权限和菜单）"""
    permissions = serializers.SerializerMethodField()
    menus = serializers.SerializerMethodField()

    class Meta(RoleSerializer.Meta):
        fields = RoleSerializer.Meta.fields + ['permissions', 'menus']

    def get_permissions(self, obj):
        return list(obj.permissions.values_list('code', flat=True))

    def get_menus(self, obj):
        return list(obj.menus.values_list('id', flat=True))
