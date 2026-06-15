"""AI audit ViewSet — /api/ai/audit/."""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ai.permissions import RootOnlyAI
from apps.ai.serializers.ai_serializers import AICallLogOutputSerializer
from apps.ai.services.ai_audit import AIAuditService


class AIAuditViewSet(viewsets.GenericViewSet):
    """AI 调用审计查询接口（仅 root）."""

    permission_classes = [RootOnlyAI]
    serializer_class = AICallLogOutputSerializer

    def list(self, request):
        """GET /api/ai/audit/ — 查询调用日志."""
        from datetime import datetime
        from django.utils.dateparse import parse_datetime

        start = request.query_params.get('start_date')
        end = request.query_params.get('end_date')
        call_type = request.query_params.get('call_type', '')
        agent_id = request.query_params.get('agent_id', '')
        root_user_id = request.query_params.get('root_user_id')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        start_dt = parse_datetime(f"{start}T00:00:00") if start else None
        end_dt = parse_datetime(f"{end}T23:59:59") if end else None

        result = AIAuditService.query_calls(
            start_date=start_dt, end_date=end_dt, call_type=call_type,
            root_user_id=int(root_user_id) if root_user_id else None,
            agent_id=agent_id, page=page, page_size=page_size,
        )
        items = AICallLogOutputSerializer(result['items'], many=True).data
        return Response({
            'data': items,
            'pagination': {
                'page': result['page'],
                'page_size': result['page_size'],
                'total': result['total'],
                'total_pages': result['total_pages'],
            },
        })

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """GET /api/ai/audit/summary/ — 审计统计摘要."""
        from django.db.models import Count, Q
        from apps.ai.models import AICallLog, AIApproval

        total_calls = AICallLog.objects.count()
        calls_by_type = list(
            AICallLog.objects.values('call_type')
            .annotate(count=Count('id')).order_by('-count')
        )
        failover_count = AICallLog.objects.filter(failover_triggered=True).count()
        pending_approvals = AIApproval.objects.filter(status='pending').count()
        approved = AIApproval.objects.filter(status__in=['approved', 'executed']).count()
        rejected = AIApproval.objects.filter(status='rejected').count()

        return Response({'data': {
            'total_calls': total_calls,
            'calls_by_type': calls_by_type,
            'failover_count': failover_count,
            'pending_approvals': pending_approvals,
            'approved': approved,
            'rejected': rejected,
        }})
