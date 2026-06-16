"""Audit log serializers."""
from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log output — includes action/resource labels."""

    action_label = serializers.SerializerMethodField()
    resource_label = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'username', 'action', 'action_label',
            'resource', 'resource_label', 'resource_id',
            'detail', 'ip_address', 'user_agent',
            'extra_data', 'created_at',
        ]

    def get_action_label(self, obj):
        return dict(AuditLog.ACTION_CHOICES).get(obj.action, obj.action)

    def get_resource_label(self, obj):
        return dict(AuditLog.RESOURCE_CHOICES).get(obj.resource, obj.resource)


class AuditLogFilterSerializer(serializers.Serializer):
    """Query parameter filter serializer for audit log list."""
    action = serializers.CharField(required=False, allow_blank=True)
    resource = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)


class AuditStatsSerializer(serializers.Serializer):
    """Audit statistics output."""
    total = serializers.IntegerField()
    by_action = serializers.DictField(child=serializers.IntegerField())
    by_resource = serializers.DictField(child=serializers.IntegerField())
    today = serializers.IntegerField()
    today_login = serializers.IntegerField()
