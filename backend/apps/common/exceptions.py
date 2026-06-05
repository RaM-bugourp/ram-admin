"""Business error and DRF exception handler."""
from rest_framework.views import exception_handler
from rest_framework.response import Response


class BusinessError(Exception):
    """Structured business exception — raised in Service layer."""

    def __init__(self, message: str, code: str = 'BUSINESS_ERROR', status: int = 400):
        self.message = message
        self.code = code
        self.status = status


def custom_exception_handler(exc, context):
    """Wrap all errors into {error: {code, message}} format."""
    # BusinessError takes priority
    if isinstance(exc, BusinessError):
        return Response(
            {'error': {'code': exc.code, 'message': exc.message}},
            status=exc.status,
        )
    # Fall back to DRF default
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(exc),
                'details': response.data,
            }
        }
    return response
