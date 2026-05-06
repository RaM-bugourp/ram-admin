import json
import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


class OperationLogMiddleware:
    """Log write operations automatically."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._log_if_needed(request, response)
        return response

    def _log_if_needed(self, request, response):
        if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return
        path = request.path
        if not path.startswith('/api/'):
            return
        # Skip login/logout to avoid recursion
        if '/auth/login/' in path or '/auth/logout/' in path:
            return

        try:
            from .models import OperationLog

            user = request.user if request.user.is_authenticated else None
            action_map = {'POST': 'create', 'PUT': 'update', 'PATCH': 'update', 'DELETE': 'delete'}
            action = action_map.get(request.method, 'other')

            request_data = None
            try:
                request_data = json.loads(request.body) if request.body else None
            except (json.JSONDecodeError, ValueError):
                pass

            OperationLog.objects.create(
                user=user,
                action=action,
                resource_type=path.split('/')[-2] if len(path.split('/')) > 2 else '',
                resource_id='',
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                request_data=request_data,
                response_status=response.status_code,
            )
        except Exception as e:
            logger.warning(f'Failed to log operation: {e}')

    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
