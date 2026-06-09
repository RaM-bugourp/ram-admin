"""Role management ViewSet — CRUD."""
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.rbac.permissions import IsAdminOrReadOnly
from apps.rbac.serializers.role_serializers import (
    RoleCreateSerializer,
    RoleUpdateSerializer,
    RoleOutputSerializer,
)
from apps.rbac.services.role_service import RoleService


class RoleViewSet(viewsets.GenericViewSet):
    """角色管理 CRUD 接口."""

    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    serializer_class = RoleOutputSerializer
    service = RoleService()

    def get_serializer_class(self):
        return {
            'create': RoleCreateSerializer,
            'update': RoleUpdateSerializer,
        }.get(self.action, RoleOutputSerializer)

    # ── GET /api/rbac/roles/ ──────────────────────────

    def list(self, request):
        """角色列表."""
        roles = self.service.list_roles()
        serializer = RoleOutputSerializer(roles, many=True)
        return Response({'data': serializer.data})

    # ── POST /api/rbac/roles/ ─────────────────────────

    def create(self, request):
        """创建角色."""
        serializer = RoleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = self.service.create_role(serializer.validated_data)
        out = RoleOutputSerializer(role)
        # 新角色无用户
        out_data = dict(out.data)
        out_data['user_count'] = 0
        return Response({'data': out_data}, status=status.HTTP_201_CREATED)

    # ── GET /api/rbac/roles/{id}/ ─────────────────────

    def retrieve(self, request, pk=None):
        """角色详情."""
        role = self.service.get_role_detail(int(pk))
        if not role:
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': '角色不存在'}},
                status=404,
            )
        serializer = RoleOutputSerializer(role)
        return Response({'data': serializer.data})

    # ── PUT /api/rbac/roles/{id}/ ─────────────────────

    def update(self, request, pk=None):
        """更新角色."""
        serializer = RoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = self.service.update_role(int(pk), serializer.validated_data)
        out = RoleOutputSerializer(role)
        return Response({'data': out.data})

    # ── DELETE /api/rbac/roles/{id}/ ──────────────────

    def destroy(self, request, pk=None):
        """删除角色."""
        self.service.delete_role(int(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)
