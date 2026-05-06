"""
apps/system/views.py — 系统管理视图（健康检查、菜单树等）
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.rbac.models import Menu


@api_view(['GET'])
@permission_classes([AllowAny])
def menu_tree(request):
    """
    GET /api/system/menu/tree/
    获取当前用户菜单树（供前端动态路由注册）。
    复用 rbac.menus.tree 的逻辑。
    """
    user = request.user
    if user.is_authenticated and user.is_superuser:
        roots = Menu.objects.filter(parent__isnull=True, is_active=True)
    elif user.is_authenticated:
        roots = Menu.objects.filter(
            parent__isnull=True, is_active=True,
            roles__in=user.roles.all()
        ).distinct()
    else:
        roots = Menu.objects.none()

    tree = [m.to_tree_node() for m in roots]
    return Response(tree)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """GET /api/system/health/ 健康检查"""
    return Response({'status': 'ok', 'version': '1.0.0'})


@api_view(['GET'])
@permission_classes([AllowAny])
def metrics(request):
    """GET /api/system/metrics/ 简单指标（可用作定时任务）"""
    from django.contrib.auth.models import User
    from apps.rbac.models import Role, Menu
    from apps.article.models import Article

    return Response({
        'total_users': User.objects.count(),
        'total_roles': Role.objects.count(),
        'total_menus': Menu.objects.count(),
        'total_articles': Article.objects.count(),
    })
