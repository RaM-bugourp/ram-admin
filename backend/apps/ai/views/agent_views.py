"""Agent token ViewSet — root signs tokens authorizing Agents."""
import uuid

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ai.permissions import RootOnlyAI, AgentTokenService
from apps.ai.serializers.ai_serializers import AgentTokenIssueSerializer, AgentTokenRevokeSerializer


class AgentTokenViewSet(viewsets.GenericViewSet):
    """Agent Token 签发接口（仅 root）."""

    permission_classes = [RootOnlyAI]
    serializer_class = AgentTokenIssueSerializer

    @action(detail=False, methods=['post'], url_path='issue')
    def issue(self, request):
        """POST /api/ai/agent-token/issue/ — root 为某个 Agent 签发授权 Token."""
        from apps.ai.services.ai_audit import AIAuditService

        serializer = AgentTokenIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        token = AgentTokenService.issue(
            root_user_id=request.user.id,
            agent_id=data['agent_id'],
            ttl_hours=data['ttl_hours'],
        )

        AIAuditService.log_call(
            root_user=request.user,
            call_type='agent_token_issue',
            prompt=f"agent_id={data['agent_id']} ttl={data['ttl_hours']}h",
            response='credential issued',
            provider='',
            failover_triggered=False,
        )

        return Response({'data': {
            'token': token,
            'token_id': str(uuid.UUID(hex=token.split('.')[1])),
            'agent_id': data['agent_id'],
            'expires_in_hours': data['ttl_hours'],
            'note': '请妥善保存，Token 仅在签发时返回一次；旧版 Token 已失效',
        }})

    @action(detail=False, methods=['post'], url_path='revoke')
    def revoke(self, request):
        serializer = AgentTokenRevokeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AgentTokenService.revoke(token_id=serializer.validated_data['token_id'], actor=request.user)
        return Response({'data': {'revoked': True}})
