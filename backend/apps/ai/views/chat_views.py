"""AI chat ViewSet — /api/ai/chat/, /api/ai/provider-status/."""
import logging
import uuid

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ai.permissions import RootOnlyAI
from apps.ai.serializers.ai_serializers import (
    AIChatRequestSerializer,
    AIProviderStatusSerializer,
)
from apps.ai.services.ai_audit import AIAuditService
from apps.ai.services.ai_errors import AIError
from apps.ai.services.ai_service import check_rate_limit, get_ai_service
from apps.ai.services.prompt_builder import build_chat_messages

logger = logging.getLogger(__name__)


class AIChatViewSet(viewsets.GenericViewSet):
    """AI 对话接口（仅 root）."""

    permission_classes = [RootOnlyAI]
    serializer_class = AIChatRequestSerializer

    @action(detail=False, methods=['post'])
    def chat(self, request):
        """POST /api/ai/chat/ — 对话主入口."""
        serializer = AIChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 频次检查
        check_rate_limit(request.user.id, is_agent=False)

        # 组装消息
        messages = build_chat_messages(data['messages'], context=data.get('context', ''))

        # 调用 AI
        service = get_ai_service()
        call_id = uuid.uuid4()
        ip = request.META.get('REMOTE_ADDR', '')

        try:
            reply, provider, failover = service.chat(
                messages, context=data.get('context', '')
            )
        except AIError:
            # 业务错误直接向上抛，由全局异常处理器转 JSON
            raise

        # 审计落库
        last_prompt = ''
        for m in reversed(data['messages']):
            if m.get('role') == 'user':
                last_prompt = m.get('content', '')
                break

        AIAuditService.log_call(
            root_user=request.user,
            call_type='chat',
            prompt=last_prompt,
            response=reply,
            provider=provider,
            failover_triggered=failover,
            call_id=call_id,
            ip_address=ip,
        )

        return Response({'data': {
            'reply': reply,
            'provider_used': provider,
            'failover_triggered': failover,
            'call_id': str(call_id),
        }})

    @action(detail=False, methods=['get'], url_path='provider-status')
    def provider_status(self, request):
        """GET /api/ai/chat/provider-status/ — Provider 池状态."""
        status = get_ai_service().get_status()
        return Response({'data': status})
