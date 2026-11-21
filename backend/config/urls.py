"""Root URL configuration."""
from django.contrib import admin
from django.urls import path, include

from apps.audit.views import AuditListView, AuditExportView, PermissionCatalogView

urlpatterns = [
    path('api/audit/logs/', AuditListView.as_view()),
    path('api/audit/export/', AuditExportView.as_view()),
    path('api/rbac/permissions/', PermissionCatalogView.as_view()),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.rbac.urls_auth')),
    path('api/rbac/users/', include('apps.rbac.urls_user')),
    path('api/rbac/roles/', include('apps.rbac.urls_role')),
    path('api/dashboard/', include('apps.rbac.urls_dashboard')),
    path('api/ai/', include('apps.ai.urls')),
]
