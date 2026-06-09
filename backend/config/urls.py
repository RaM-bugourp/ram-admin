"""Root URL configuration."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.rbac.urls_auth')),
    path('api/rbac/users/', include('apps.rbac.urls_user')),
    path('api/rbac/roles/', include('apps.rbac.urls_role')),
    path('api/dashboard/', include('apps.rbac.urls_dashboard')),
]
