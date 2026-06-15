"""AI approval ViewSet — submit / list / review / detail."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ai.permissions import RootOnlyAI, RootOrAgentAuth
from apps.ai.serializers.ai_serializers import (
    AIApprovalOutputSerializer,
    AIApprovalReviewSerializer,
    AIApprovalSubmitSerializer,
)
from apps.ai.services.ai_approval import AIApprovalService
from apps.ai.services.ai_audit import AIAuditService


class AIApprovalViewSet(viewsets.GenericViewSet):
    """Agent 操作审批接口.

    - submit: root 或携带 Agent Token 的 Agent 都可提交
    - list / retrieve / review: 仅 root
    """

    serializer_class = AIApprovalOutputSerializer

    def get_permissions(self):
        if self.action == 'submit':
            return [RootOrAgentAuth()]
        return [RootOnlyAI()]

    @property
    def service(self):
        return AIApprovalService()

    # ── POST /api/ai/approval/submit/ ──────────────────────

    @action(detail=False, methods=['post'])
    def submit(self, request):
        serializer = AIApprovalSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 判断来源：root 直接提交 vs Agent Token 提交
        agent_payload = getattr(request, '_agent_payload', None)
        if agent_payload:
            agent_id = agent_payload.get('agent_id') or data['agent_id']
            root_user = None  # Agent 提交，root_user 置空
        else:
            agent_id = data['agent_id']
            root_user = request.user

        approval = self.service.submit_operation(
            agent_id=agent_id,
            operation=data['operation'],
            params=data.get('params') or {},
            reason=data.get('reason', ''),
            root_user=root_user,
        )

        # 审计：Agent 代发日志
        AIAuditService.log_agent_submission(
            agent_id=agent_id,
            operation=data['operation'],
            params=data.get('params') or {},
            approval_id=approval.id,
        )

        out = AIApprovalOutputSerializer(approval)
        return Response({'data': out.data}, status=status.HTTP_201_CREATED)

    # ── GET /api/ai/approval/ ──────────────────────────────

    def list(self, request):
        status_filter = request.query_params.get('status', '')
        agent_id = request.query_params.get('agent_id', '')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        result = self.service.list_approvals(
            status_filter=status_filter, agent_id=agent_id,
            page=page, page_size=page_size,
        )
        items = AIApprovalOutputSerializer(result['items'], many=True).data
        return Response({
            'data': items,
            'pagination': {
                'page': result['page'],
                'page_size': result['page_size'],
                'total': result['total'],
                'total_pages': result['total_pages'],
            },
        })

    # ── GET /api/ai/approval/{id}/ ─────────────────────────

    def retrieve(self, request, pk=None):
        approval = self.service.get_detail(int(pk))
        out = AIApprovalOutputSerializer(approval)
        return Response({'data': out.data})

    # ── POST /api/ai/approval/{id}/review/ ─────────────────

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        serializer = AIApprovalReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        approval = self.service.review(
            approval_id=int(pk),
            root_user=request.user,
            action=data['action'],
            comment=data.get('comment', ''),
            ip_address=request.META.get('REMOTE_ADDR', ''),
        )
        out = AIApprovalOutputSerializer(approval)
        return Response({'data': out.data})
