from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, MenuViewSet, PermissionViewSet, RoleViewSet

router = DefaultRouter()
router.register('organizations', OrganizationViewSet, basename='organization')
router.register('menus', MenuViewSet, basename='menu')
router.register('permissions', PermissionViewSet, basename='permission')
router.register('roles', RoleViewSet, basename='role')

urlpatterns = [path('', include(router.urls))]
