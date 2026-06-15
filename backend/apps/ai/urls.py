"""AI URL routing.

/api/ai/chat/                 → AIChatViewSet (chat / provider-status)
/api/ai/analyze/              → AIAnalyzeViewSet (analyze / insights)
/api/ai/report/               → AIReportViewSet (report)
/api/ai/approval/             → AIApprovalViewSet (submit / list / review / detail)
/api/ai/audit/                → AIAuditViewSet (list / summary)
/api/ai/notifications/        → AINotificationViewSet (list / read / read-all)
/api/ai/agent-token/          → AgentTokenViewSet (issue)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.ai.views import (
    AIChatViewSet,
    AIAnalyzeViewSet,
    AIReportViewSet,
    AIApprovalViewSet,
    AIAuditViewSet,
    AINotificationViewSet,
    AgentTokenViewSet,
)

router = DefaultRouter()
router.register(r'chat', AIChatViewSet, basename='ai-chat')
router.register(r'analyze', AIAnalyzeViewSet, basename='ai-analyze')
router.register(r'report', AIReportViewSet, basename='ai-report')
router.register(r'approval', AIApprovalViewSet, basename='ai-approval')
router.register(r'audit', AIAuditViewSet, basename='ai-audit')
router.register(r'notifications', AINotificationViewSet, basename='ai-notification')
router.register(r'agent-token', AgentTokenViewSet, basename='ai-agent-token')

urlpatterns = [
    path('', include(router.urls)),
]
