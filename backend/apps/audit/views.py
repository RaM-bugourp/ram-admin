"""Audit log ViewSet — list, stats, cleanup."""
from datetime import date, timedelta

from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.audit.models import AuditLog
from apps.audit.serializers import (
    AuditLogFilterSerializer,
    AuditLogSerializer,
    AuditStatsSerializer,
)
from apps.rbac.permissions import IsAdminOrReadOnly


class AuditLogViewSet(GenericViewSet):
    """审计日志 — 列表 / 统计 / 清理."""

    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    serializer_class = AuditLogSerializer

    # ── GET /api/audit/logs/ ─────────────────────────────

    def list(self, request):
        """审计日志列表 — 支持 action/resource/username/日期范围过滤."""
        filter_serializer = AuditLogFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        params = filter_serializer.validated_data

        qs = AuditLog.objects.all()

        action = params.get('action')
        if action:
            qs = qs.filter(action=action)

        resource = params.get('resource')
        if resource:
            qs = qs.filter(resource=resource)

        username = params.get('username')
        if username:
            qs = qs.filter(username__icontains=username)

        start_date = params.get('start_date')
        end_date = params.get('end_date')
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        page = params.get('page', 1)
        page_size = params.get('page_size', 20)
        total = qs.count()
        start = (page - 1) * page_size
        items = list(qs[start:start + page_size])
        serializer = AuditLogSerializer(items, many=True)

        return Response({
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size,
            },
        })

    # ── GET /api/audit/logs/stats/ ────────────────────

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """审计统计 — 总量 / 按操作类型 / 按资源 / 今日登录数."""
        today = date.today()
        qs = AuditLog.objects.all()

        by_action = dict(
            qs.values_list('action')
              .annotate(cnt=Count('id'))
              .values_list('action', 'cnt')
        )
        by_resource = dict(
            qs.values_list('resource')
              .annotate(cnt=Count('id'))
              .values_list('resource', 'cnt')
        )
        today_count = qs.filter(created_at__date=today).count()
        today_login = qs.filter(
            created_at__date=today, action='LOGIN'
        ).count()

        data = {
            'total': qs.count(),
            'by_action': by_action,
            'by_resource': by_resource,
            'today': today_count,
            'today_login': today_login,
        }
        serializer = AuditStatsSerializer(data=data)
        return Response({'data': serializer.data})

    # ── DELETE /api/audit/logs/cleanup/ ───────────────

    @action(detail=False, methods=['delete'], url_path='cleanup')
    def cleanup(self, request):
        """清理 N 天之前的日志（默认 90 天）."""
        days = int(request.query_params.get('days', 90))
        cutoff = date.today() - timedelta(days=days)
        deleted, _ = AuditLog.objects.filter(
            created_at__date__lt=cutoff
        ).delete()
        return Response({
            'data': {'deleted': deleted, 'cutoff_days': days},
        })

    # ── GET /api/audit/logs/actions/ ──────────────────

    @action(detail=False, methods=['get'], url_path='actions')
    def actions(self, _request):
        """返回所有操作类型选项，供前端下拉框使用."""
        return Response({
            'data': [{'value': k, 'label': v}
                     for k, v in AuditLog.ACTION_CHOICES],
        })

    # ── GET /api/audit/logs/resources/ ───────────────

    @action(detail=False, methods=['get'], url_path='resources')
    def resources(self, _request):
        """返回所有资源类型选项."""
        return Response({
            'data': [{'value': k, 'label': v}
                     for k, v in AuditLog.RESOURCE_CHOICES],
        })