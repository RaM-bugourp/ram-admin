"""
apps/rbac/views.py — RBAC 权限管理视图
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Organization, Menu, Permission, Role
from .serializers import (
    OrganizationSerializer, MenuSerializer, MenuTreeSerializer,
    PermissionSerializer, RoleSerializer, RoleDetailSerializer,
)


class OrganizationViewSet(viewsets.ModelViewSet):
    """组织管理"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    pagination_class = None    # 组织树不分页
    filterset_fields = ['name', 'code', 'is_active']
    ordering_fields = ['sort', 'id']

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """GET /api/rbac/organizations/tree/ 获取组织树"""
        roots = Organization.objects.filter(parent__isnull=True, is_active=True)
        tree = [org.to_tree_node() for org in roots]
        return Response(tree)


class MenuViewSet(viewsets.ModelViewSet):
    """菜单管理"""
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    pagination_class = None
    filterset_fields = ['title', 'is_active']
    ordering_fields = ['sort', 'id']

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def tree(self, request):
        """
        GET /api/rbac/menus/tree/
        获取当前用户的菜单树（用于前端动态路由注册）。

        注意：这个接口在 router beforeEach 里调用！
        必须返回完整的菜单结构（含 component 路径）。
        """
        user = request.user
        if user.is_superuser:
            # 超管：返回所有启用的菜单
            roots = Menu.objects.filter(parent__isnull=True, is_active=True)
        else:
            # 普通用户：只返回其角色关联的菜单
            roots = Menu.objects.filter(
                parent__isnull=True,
                is_active=True,
                roles__in=user.roles.all()
            ).distinct()

        tree = [menu.to_tree_node() for menu in roots]
        return Response(tree)


class PermissionViewSet(viewsets.ModelViewSet):
    """权限管理"""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    filterset_fields = ['name', 'code', 'ptype', 'is_active']
    ordering_fields = ['sort', 'id']

    @action(detail=False, methods=['get'])
    def code_tree(self, request):
        """GET /api/rbac/permissions/code_tree/ 获取权限码树（用于角色授权）"""
        queryset = self.get_queryset().filter(is_active=True)
        tree = _build_permission_tree(queryset)
        return Response(tree)


class RoleViewSet(viewsets.ModelViewSet):
    """角色管理"""
    queryset = Role.objects.all()
    filterset_fields = ['name', 'code', 'is_active']
    ordering_fields = ['sort', 'id']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RoleDetailSerializer
        return RoleSerializer

    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        """POST /api/rbac/roles/{pk}/assign_permissions/ 分配权限"""
        role = self.get_object()
        permission_ids = request.data.get('permission_ids', [])
        role.permissions.set(permission_ids)
        return Response({'message': '权限分配成功'})

    @action(detail=True, methods=['post'])
    def assign_menus(self, request, pk=None):
        """POST /api/rbac/roles/{pk}/assign_menus/ 分配菜单"""
        role = self.get_object()
        menu_ids = request.data.get('menu_ids', [])
        role.menus.set(menu_ids)
        return Response({'message': '菜单分配成功'})


def _build_permission_tree(queryset):
    """构建权限树（按 app:model 分组）"""
    groups = {}
    for perm in queryset:
        parts = perm.code.split(':')
        if len(parts) >= 2:
            group = parts[0]   # app
            subgroup = f'{parts[0]}:{parts[1]}'  # app:model
        else:
            group = 'other'
            subgroup = 'other'
        if subgroup not in groups:
            groups[subgroup] = {'title': subgroup, 'key': subgroup, 'children': []}
        groups[subgroup]['children'].append({
            'key': perm.code,
            'title': perm.name,
            'id': perm.id,
        })
    return list(groups.values())
