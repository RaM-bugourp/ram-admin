"""AI serializers — chat, approval, audit, notification."""
from rest_framework import serializers

from apps.ai.models import AICallLog, AIApproval, AIApprovalLog, Notification


# ── 对话 ────────────────────────────────────────────────────────

class AIChatMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['user', 'assistant', 'system'])
    content = serializers.CharField()


class AIChatRequestSerializer(serializers.Serializer):
    """POST /api/ai/chat/ 输入契约."""

    messages = AIChatMessageSerializer(many=True)
    context = serializers.CharField(required=False, allow_blank=True, default='')
    stream = serializers.BooleanField(required=False, default=False)
    agent_mode = serializers.BooleanField(required=False, default=False)


class AIChatResponseSerializer(serializers.Serializer):
    reply = serializers.CharField()
    provider_used = serializers.CharField()
    failover_triggered = serializers.BooleanField()
    call_id = serializers.CharField()
    data = serializers.JSONField(required=False)


class AIProviderStatusSerializer(serializers.Serializer):
    providers = serializers.ListField()
    current_provider = serializers.CharField()
    failover_triggered = serializers.BooleanField()
    mock_mode = serializers.BooleanField()


# ── 审批 ────────────────────────────────────────────────────────

class AIApprovalSubmitSerializer(serializers.Serializer):
    """Agent 提交审批输入."""

    agent_id = serializers.CharField(max_length=100)
    operation = serializers.CharField(max_length=100)
    params = serializers.JSONField(default=dict)
    reason = serializers.CharField(required=False, allow_blank=True, default='')


class AIApprovalReviewSerializer(serializers.Serializer):
    """Root 审批输入."""

    action = serializers.ChoiceField(choices=['approve', 'reject'])
    comment = serializers.CharField(required=False, allow_blank=True, default='')


class AIApprovalOutputSerializer(serializers.ModelSerializer):
    params = serializers.SerializerMethodField()

    def get_params(self, obj):
        from apps.ai.services.approval_params import safe_params
        return safe_params(obj.operation, obj.params)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['submitted_by'] = instance.submitted_by_id
        data['attribution'] = 'known' if instance.submitted_by_id else 'unknown-legacy'
        # Free text may contain historical secrets; never echo it through audit/review APIs.
        data['reason'] = '[REDACTED]' if instance.reason else ''
        data['approver_comment'] = '[REDACTED]' if instance.approver_comment else ''
        data['execution_error'] = 'EXECUTION_FAILED' if instance.execution_error else ''
        return data

    approved_by_name = serializers.SerializerMethodField()
    approval_uid = serializers.CharField(read_only=True)

    class Meta:
        model = AIApproval
        fields = [
            'id', 'approval_uid', 'agent_id', 'operation', 'params', 'reason',
            'status', 'approved_by', 'approved_by_name', 'approved_at',
            'approver_comment', 'executed_at', 'execution_error',
            'created_at', 'updated_at',
        ]

    def get_approved_by_name(self, obj) -> str:
        return obj.approved_by.username if obj.approved_by else ''


class AIApprovalLogOutputSerializer(serializers.ModelSerializer):
    root_user_name = serializers.SerializerMethodField()

    class Meta:
        model = AIApprovalLog
        fields = [
            'id', 'approval', 'root_user', 'root_user_name',
            'action', 'comment', 'ip_address', 'created_at',
        ]

    def get_root_user_name(self, obj) -> str:
        return obj.root_user.username if obj.root_user_id else ''


# ── 审计 ────────────────────────────────────────────────────────

class AICallLogOutputSerializer(serializers.ModelSerializer):
    root_user_name = serializers.SerializerMethodField()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.call_type == 'agent_submission':
            data['prompt'] = '[REDACTED agent submission]'
            data['response'] = '[REDACTED]'
        return data

    class Meta:
        model = AICallLog
        fields = [
            'id', 'call_id', 'root_user', 'root_user_name', 'agent_id',
            'call_type', 'prompt', 'response', 'provider_used',
            'failover_triggered', 'tokens_used', 'cost', 'ip_address',
            'created_at',
        ]

    def get_root_user_name(self, obj) -> str:
        return obj.root_user.username if obj.root_user_id else ''


# ── 通知 ────────────────────────────────────────────────────────

class NotificationOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'level', 'is_read', 'created_at',
        ]


# ── 分析 / 报告 ────────────────────────────────────────────────

class AIAnalyzeRequestSerializer(serializers.Serializer):
    question = serializers.CharField(min_length=2)


class AIReportRequestSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(
        choices=['user_activity', 'role_distribution', 'system_overview']
    )


# ── Agent Token ────────────────────────────────────────────────

class AgentTokenIssueSerializer(serializers.Serializer):
    agent_id = serializers.CharField(max_length=100)
    ttl_hours = serializers.IntegerField(required=False, default=24, min_value=1, max_value=720)


class AgentTokenIssueResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    token_id = serializers.UUIDField()
    expires_in_hours = serializers.IntegerField()
    agent_id = serializers.CharField()


class AgentTokenRevokeSerializer(serializers.Serializer):
    token_id = serializers.UUIDField()
