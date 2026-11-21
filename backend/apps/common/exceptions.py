"""Structured error contract and safe API failure audit."""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response

class BusinessError(Exception):
    def __init__(self,message,code='BUSINESS_ERROR',status=400):
        self.message=message;self.code=code;self.status=status
        super().__init__(message)

def custom_exception_handler(exc,context):
    response=Response({'error':{'code':exc.code,'message':exc.message}},status=exc.status) if isinstance(exc,BusinessError) else exception_handler(exc,context)
    if response is None:return None
    request=context.get('request')
    if response.status_code>=400 and request and not getattr(request,'_login_event_recorded',False) and request.path.startswith(('/api/rbac/','/api/auth/','/api/audit/')):
        # Service @atomic has unwound before this handler. No request data, values or path IDs.
        from apps.rbac.permissions import effective_user
        from apps.audit import service as audit
        actor=effective_user(request.user)
        try:audit.record(actor,'request.rejected' if response.status_code<500 else 'request.failed','api',outcome='denied' if response.status_code in (401,403) else 'failed')
        except Exception:logging.getLogger(__name__).error('Safe failure audit unavailable')
    if not isinstance(exc,BusinessError):
        status=response.status_code;code='CSRF_FAILED' if 'csrf' in str(exc).lower() else 'PERMISSION_DENIED' if status==403 else 'NOT_FOUND' if status==404 else 'VALIDATION_ERROR'
        response.data={'error':{'code':code,'message':str(exc)}}
    return response
