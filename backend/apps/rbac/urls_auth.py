"""Auth URL routing."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.rbac.views import AuthViewSet

router = DefaultRouter()
router.register(r'', AuthViewSet, basename='auth')

urlpatterns = [
    path('', include(router.urls)),
]
