"""AI analyze & report ViewSets — /api/ai/analyze/, /api/ai/report/, /api/ai/insights/."""
import json
import logging
import uuid

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ai.permissions import RootOnlyAI
from apps.ai.serializers.ai_serializers import (
    AIAnalyzeRequestSerializer,
    AIReportRequestSerializer,
)
from apps.ai.services.ai_audit import AIAuditService
from apps.ai.services.ai_service import get_ai_service
from apps.ai.services.data_formatter import sanitize_data
from apps.ai.services.prompt_builder import (
    build_analyze_prompt,
    build_insight_prompt,
    build_report_prompt,
)
from apps.ai.services.stats_service import (
    collect_dashboard_stats,
    collect_report_data,
)

logger = logging.getLogger(__name__)


class AIAnalyzeViewSet(viewsets.GenericViewSet):
    """数据分析接口（仅 root）."""

    permission_classes = [RootOnlyAI]
    serializer_class = AIAnalyzeRequestSerializer

    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """POST /api/ai/analyze/ — 基于系统数据回答分析问题."""
        serializer = AIAnalyzeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data['question']

        # 采集并脱敏数据
        stats = sanitize_data(collect_dashboard_stats())
        messages = build_analyze_prompt(question, stats)

        service = get_ai_service()
        call_id = uuid.uuid4()
        reply, provider, failover = service.chat(messages)

        AIAuditService.log_call(
            root_user=request.user,
            call_type='analyze',
            prompt=question,
            response=reply,
            provider=provider,
            failover_triggered=failover,
            call_id=call_id,
            ip_address=request.META.get('REMOTE_ADDR', ''),
        )

        return Response({'data': {
            'reply': reply,
            'provider_used': provider,
            'failover_triggered': failover,
            'call_id': str(call_id),
            'data': stats,
        }})

    @action(detail=False, methods=['get'])
    def insights(self, request):
        """GET /api/ai/analyze/insights/ — 仪表盘 AI 洞察."""
        stats = sanitize_data(collect_dashboard_stats())
        messages = [{'role': 'user', 'content': build_insight_prompt(stats)}]

        service = get_ai_service()
        call_id = uuid.uuid4()
        reply, provider, failover = service.chat(messages, temperature=0.3)

        AIAuditService.log_call(
            root_user=request.user,
            call_type='analyze',
            prompt='dashboard_insights',
            response=reply,
            provider=provider,
            failover_triggered=failover,
            call_id=call_id,
            ip_address=request.META.get('REMOTE_ADDR', ''),
        )

        # 尝试解析为结构化 insights（失败则把整段文本作为单条 insight 返回）
        insights = _try_parse_insights(reply)

        return Response({'data': {
            'insights': insights,
            'raw': reply,
            'provider_used': provider,
            'call_id': str(call_id),
        }})


class AIReportViewSet(viewsets.GenericViewSet):
    """报告生成接口（仅 root）."""

    permission_classes = [RootOnlyAI]
    serializer_class = AIReportRequestSerializer

    @action(detail=False, methods=['post'])
    def report(self, request):
        """POST /api/ai/report/ — 生成 Markdown 报告."""
        serializer = AIReportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report_type = serializer.validated_data['report_type']

        data = sanitize_data(collect_report_data(report_type))
        messages = build_report_prompt(report_type, data)

        service = get_ai_service()
        call_id = uuid.uuid4()
        reply, provider, failover = service.chat(messages, temperature=0.4)

        AIAuditService.log_call(
            root_user=request.user,
            call_type='report',
            prompt=f'report:{report_type}',
            response=reply,
            provider=provider,
            failover_triggered=failover,
            call_id=call_id,
            ip_address=request.META.get('REMOTE_ADDR', ''),
        )

        return Response({'data': {
            'report': reply,
            'report_type': report_type,
            'provider_used': provider,
            'call_id': str(call_id),
        }})


def _try_parse_insights(text: str) -> list[dict]:
    """尝试从 AI 回复中提取 JSON 数组形式的 insights."""
    try:
        # 容忍前后可能有 ``` 代码块包裹
        cleaned = text.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('\n', 1)[-1] if '\n' in cleaned else cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed
    except (ValueError, json.JSONDecodeError):
        pass
    # 回退：整段文本作为单条 insight
    return [{'insight': text.strip(), 'level': 'info'}]
