"""Auth views — login, logout, user-info."""
import logging
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from apps.common.exceptions import BusinessError
from apps.rbac.models import User

logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.GenericViewSet):
    """Authentication endpoints."""

    def get_permissions(self):
        if self.action in ('login',):
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'])
    def login(self, request):
        """POST /api/auth/login/ — Session-based login."""
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            raise BusinessError(
                message='用户名和密码不能为空',
                code='INVALID_CREDENTIALS',
                status=400,
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            raise BusinessError(
                message='用户名或密码错误',
                code='INVALID_CREDENTIALS',
                status=401,
            )
        if not user.is_active:
            raise BusinessError(
                message='用户已被禁用',
                code='USER_INACTIVE',
                status=403,
            )

        login(request, user)
        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])

        logger.info('User logged in', extra={'user_id': user.id, 'username': user.username})

        return Response({
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
            }
        })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """POST /api/auth/logout/ — Clear session."""
        logout(request)
        return Response({'data': {}})

    @action(detail=False, methods=['get'], url_path='user-info')
    def user_info(self, request):
        """GET /api/auth/user-info/ — Current user info."""
        user = request.user
        return Response({
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
                'permissions': [],  # placeholder — RBAC not yet built
            }
        })
