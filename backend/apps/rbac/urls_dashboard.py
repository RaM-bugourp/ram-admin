from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views.dashboard_views import DashboardViewSet

router = SimpleRouter()
router.register(r'', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
