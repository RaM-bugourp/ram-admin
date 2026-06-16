"""Audit logging utility — call from views/services to record events."""
from apps.audit.models import AuditLog


def get_client_ip(request):
    """Extract client IP from request, respecting X-Forwarded-For."""
    if not request:
        return None
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_audit(user, action, resource, resource_id=None, detail='',
              extra_data=None, request=None):
    """Create an audit log entry. Safe to call without request (e.g., celery tasks)."""
    AuditLog.objects.create(
        user=user,
        username=user.username if user else 'system',
        action=action,
        resource=resource,
        resource_id=str(resource_id) if resource_id else None,
        detail=detail,
        ip_address=get_client_ip(request),
        user_agent=(request.META.get('HTTP_USER_AGENT', '')[:500]
                    if request else ''),
        extra_data=extra_data or {},
    )
