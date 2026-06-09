"""Dashboard ViewSet — aggregate stats."""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.rbac.models import User, Role, UserRole


class DashboardViewSet(viewsets.GenericViewSet):
    """Dashboard 统计接口."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """聚合统计数据."""
        total_users = User.objects.filter(is_deleted=False).count()
        active_users = User.objects.filter(is_deleted=False, is_active=True).count()
        total_roles = Role.objects.count()
        total_assignments = UserRole.objects.count()

        return Response({'data': {
            'total_users': total_users,
            'active_users': active_users,
            'total_roles': total_roles,
            'total_assignments': total_assignments,
        }})
