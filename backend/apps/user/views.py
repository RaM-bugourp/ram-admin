"""
User 视图集 — 认证接口 + 用户管理
"""

from django.contrib.auth import login as django_login, logout as django_logout
from django.middleware.csrf import get_token
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import User
from .serializers import LoginSerializer, UserInfoSerializer, UserListSerializer


class AuthViewSet(viewsets.GenericViewSet):
    """
    认证相关接口（登录/登出/用户信息）

    为什么不放在 UserViewSet 里？
        —— 认证接口不需要 RBAC 权限，任何人都能访问
        —— 单独一个 ViewSet 可以更灵活地配置权限
    """
    permission_classes = [AllowAny]    # 认证接口无需登录

    @action(detail=False, methods=['post'], authentication_classes=[])
    def login(self, request):
        """
        POST /api/auth/login/
        登录接口。
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # Django 内置认证（检查 username + password）
        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {'detail': '用户名或密码错误'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'detail': '账户已被禁用'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Django Session 登录（写 Session 到 DB + 返回 Cookie）
        django_login(request, user)

        # 设置 CSRF token cookie，供前端后续请求使用
        get_token(request)

        # 返回用户信息
        info_serializer = UserInfoSerializer(user)
        return Response({
            'message': '登录成功',
            'user': info_serializer.data,
        })

    @action(detail=False, methods=['post'], authentication_classes=[])
    def logout(self, request):
        """
        POST /api/auth/logout/
        登出接口。
        """
        django_logout(request)
        return Response({'message': '登出成功'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def user_info(self, request):
        """
        GET /api/auth/user_info/
        获取当前登录用户信息（前端初始化时调用）。
        """
        serializer = UserInfoSerializer(request.user)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    用户管理接口（CRUD）。

    完整 CRUD：
      GET    /api/users/          列表
      POST   /api/users/          创建
      GET    /api/users/{pk}/     详情
      PUT    /api/users/{pk}/     更新
      DELETE /api/users/{pk}/     删除
    """
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    filterset_fields = ['username', 'email', 'is_active', 'is_superuser']
    search_fields = ['username', 'email', 'phone']
    ordering_fields = ['id', 'username', 'date_joined', 'last_login']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserInfoSerializer
        return UserListSerializer

    def perform_create(self, serializer):
        # 创建用户时设置密码（hash 处理）
        password = self.request.data.get('password')
        user = serializer.save()
        if password:
            user.set_password(password)
            user.save(update_fields=['password'])

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """POST /api/users/{pk}/reset_password/ 重置密码"""
        user = self.get_object()
        new_password = request.data.get('new_password')
        if not new_password or len(new_password) < 6:
            return Response({'detail': '密码至少6位'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response({'message': '密码已重置'})
