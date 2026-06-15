"""AI notification ViewSet — /api/ai/notifications/."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ai.models import Notification
from apps.ai.permissions import RootOnlyAI
from apps.ai.serializers.ai_serializers import NotificationOutputSerializer


class AINotificationViewSet(viewsets.GenericViewSet):
    """AI 站内通知接口（仅 root）."""

    permission_classes = [RootOnlyAI]
    serializer_class = NotificationOutputSerializer

    def list(self, request):
        """GET /api/ai/notifications/ — 当前用户的通知列表."""
        only_unread = request.query_params.get('unread') in ('1', 'true', 'True')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        qs = Notification.objects.filter(recipient=request.user)
        if only_unread:
            qs = qs.filter(is_read=False)

        from django.core.paginator import Paginator
        paginator = Paginator(qs, min(page_size, 100))
        page_obj = paginator.get_page(page)

        items = NotificationOutputSerializer(page_obj.object_list, many=True).data
        unread_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()

        return Response({
            'data': items,
            'pagination': {
                'page': page_obj.number,
                'page_size': min(page_size, 100),
                'total': paginator.count,
                'total_pages': paginator.num_pages,
            },
            'unread_count': unread_count,
        })

    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        """POST /api/ai/notifications/{id}/read/ — 标记已读."""
        try:
            n = Notification.objects.get(id=pk, recipient=request.user)
        except Notification.DoesNotExist:
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': '通知不存在'}},
                status=404,
            )
        n.mark_read()
        return Response({'data': {'id': n.id, 'is_read': True}})

    @action(detail=False, methods=['post'], url_path='read-all')
    def mark_all_read(self, request):
        """POST /api/ai/notifications/read-all/ — 全部标记已读."""
        updated = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        return Response({'data': {'updated': updated}})
