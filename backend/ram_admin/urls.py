"""
Django 主 URL 配置
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# ═══════════════════════════════════════════════════════════
# 全局 API 路由
# ═══════════════════════════════════════════════════════════

# DRF Router：自动生成 CRUD 路由
# /api/users/          GET(list) / POST(create)
# /api/users/{pk}/    GET(retrieve) / PUT(update) / PATCH(partial_update) / DELETE(destroy)

router = DefaultRouter()


# ═══════════════════════════════════════════════════════════
# URL 路由定义
# ═══════════════════════════════════════════════════════════

urlpatterns = [
    # DRF 自动路由（放在最前，优先匹配）
    path('api/', include(router.urls)),

    # Django Admin（可选）
    path('admin/', admin.site.urls),

    # 各业务模块 URL
    path('api/auth/', include('apps.user.urls')),
    path('api/rbac/', include('apps.rbac.urls')),
    path('api/system/', include('apps.system.urls')),
    path('api/article/', include('apps.article.urls')),

    # API 文档（Swagger UI）
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # 健康检查（负载均衡探活用）
    path('health/', api_view(['GET'])(lambda r: Response({'status': 'ok'}))),
]


# ═══════════════════════════════════════════════════════════
# FAQ：path 和 include 的区别？
#
# path('api/auth/', include('apps.user.urls'))
#   —— 把 apps.user.urls 里的所有路由加上前缀 'api/auth/'
#   —— urls.py 里的 path('login/') → 最终变成 /api/auth/login/
#
# include((urlpatterns, app_name), namespace='xxx')
#   —— 可以给 app 的 URL 加上命名空间，避免冲突
#   —— 模板中用 {% url 'user:login' %}
# ═══════════════════════════════════════════════════════════
