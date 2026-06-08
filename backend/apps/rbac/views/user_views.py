"""User management ViewSet — CRUD + password reset."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.rbac.serializers.user_serializers import (
    UserCreateSerializer,
    UserUpdateSerializer,
    UserResetPasswordSerializer,
    UserOutputSerializer,
)
from apps.rbac.services.user_service import UserService


class UserViewSet(viewsets.GenericViewSet):
    """用户管理 CRUD 接口."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserOutputSerializer
    service = UserService()

    def get_serializer_class(self):
        return {
            'create': UserCreateSerializer,
            'update': UserUpdateSerializer,
            'reset_password': UserResetPasswordSerializer,
        }.get(self.action, UserOutputSerializer)

    # ── GET /api/rbac/users/ ─────────────────────────────

    def list(self, request):
        """用户列表（分页 + 搜索）."""
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        search = request.query_params.get('search', '')

        result = self.service.list_users(page=page, page_size=page_size, search=search)
        serializer = UserOutputSerializer(result['items'], many=True)

        return Response({
            'data': serializer.data,
            'pagination': {
                'page': result['page'],
                'page_size': result['page_size'],
                'total': result['total'],
                'total_pages': result['total_pages'],
            },
        })

    # ── POST /api/rbac/users/ ────────────────────────────

    def create(self, request):
        """创建用户."""
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.service.create_user(serializer.validated_data)
        out = UserOutputSerializer(user)
        return Response({'data': out.data}, status=status.HTTP_201_CREATED)

    # ── GET /api/rbac/users/{id}/ ────────────────────────

    def retrieve(self, request, pk=None):
        """用户详情."""
        user = self.service.get_user_detail(int(pk))
        if not user:
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': '用户不存在'}},
                status=404,
            )
        serializer = UserOutputSerializer(user)
        return Response({'data': serializer.data})

    # ── PUT /api/rbac/users/{id}/ ────────────────────────

    def update(self, request, pk=None):
        """更新用户."""
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.service.update_user(int(pk), serializer.validated_data)
        out = UserOutputSerializer(user)
        return Response({'data': out.data})

    # ── DELETE /api/rbac/users/{id}/ ─────────────────────

    def destroy(self, request, pk=None):
        """软删除用户."""
        self.service.delete_user(int(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── POST /api/rbac/users/{id}/reset-password/ ────────

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        """重置密码."""
        serializer = UserResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.service.reset_password(int(pk), serializer.validated_data['password'])
        return Response({'data': {'message': '密码重置成功'}})
