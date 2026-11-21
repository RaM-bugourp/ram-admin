"""Dashboard ViewSet — aggregate stats."""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.rbac.models import User, Role, UserRole
from apps.rbac.permissions import EffectiveAuthenticated, permission_codes


class DashboardViewSet(viewsets.GenericViewSet):
    """Dashboard 统计接口."""

    permission_classes = [EffectiveAuthenticated]

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """聚合统计数据."""
        if 'users.read' not in permission_codes(request.user):
            return Response({'data': {'total_users': None,'active_users': None,'total_roles': None,'total_assignments': None}})
        total_users = User.objects.filter(is_deleted=False).count()
        active_users = User.objects.filter(is_deleted=False, is_active=True).count()
        total_roles = Role.objects.count()
        total_assignments = UserRole.objects.filter(user__is_deleted=False,role__is_deleted=False).count()

        return Response({'data': {
            'total_users': total_users,
            'active_users': active_users,
            'total_roles': total_roles,
            'total_assignments': total_assignments,
        }})
