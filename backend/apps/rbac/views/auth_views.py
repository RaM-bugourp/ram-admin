"""Auth views — login, logout, user-info."""
import logging
from django.contrib.auth import authenticate, login, logout
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from apps.common.exceptions import BusinessError

logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.GenericViewSet):
    """Authentication endpoints."""

    def get_permissions(self):
        if self.action in ('login', 'csrf_token'):
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='csrf')
    def csrf_token(self, request):
        from django.middleware.csrf import get_token
        get_token(request)
        return Response({'data': {}})

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        if not username or not password:
            raise BusinessError(message='用户名和密码不能为空', code='INVALID_CREDENTIALS', status=400)
        user = authenticate(request, username=username, password=password)
        if user is None:
            raise BusinessError(message='用户名或密码错误', code='INVALID_CREDENTIALS', status=401)
        if not user.is_active:
            raise BusinessError(message='用户已被禁用', code='USER_INACTIVE', status=403)
        login(request, user)
        logger.info('User logged in', extra={'user_id': user.id, 'username': user.username})
        from apps.rbac.models import UserRole
        user_roles = UserRole.objects.select_related('role').filter(user=user)
        roles = [{'id': ur.role_id, 'name': ur.role.name, 'code': ur.role.code} for ur in user_roles]
        return Response({'data': {
            'id': user.id, 'username': user.username, 'email': user.email,
            'is_superuser': user.is_superuser,
            'roles': roles,
        }})

    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response({'data': {}})

    @action(detail=False, methods=['get'], url_path='user-info')
    def user_info(self, request):
        user = request.user
        from apps.rbac.models import UserRole
        user_roles = UserRole.objects.select_related('role').filter(user=user)
        roles = [{'id': ur.role_id, 'name': ur.role.name, 'code': ur.role.code} for ur in user_roles]
        return Response({'data': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_superuser': user.is_superuser,
            'roles': roles,
            'permissions': [],
        }})
