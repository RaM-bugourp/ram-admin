"""
core/exceptions.py — 全局异常处理
══════════════════════════════════════════════════════════════════

Django REST Framework 的默认异常格式是：
  { "detail": "错误信息" }

这里自定义为更友好的格式：
  { "code": "ERROR_CODE", "message": "友好的中文提示" }

为什么要自定义？
  —— 方便前端做错误码判断（不只是看字符串）
  —— 统一前端和后端的错误格式
"""

from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    ValidationError, NotAuthenticated, AuthenticationFailed,
    PermissionDenied, NotFound, MethodNotAllowed, Throttled,
)
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    DRF 全局异常处理器（注册在 settings.py 的 REST_FRAMEWORK.EXCEPTION_HANDLER）。

    执行顺序：
      View 发生异常
        → DRF 调用 custom_exception_handler(exc, context)
        → 这里处理已知异常，返回格式化响应
        → 如果无法处理，调用 DRF 默认处理器
    """
    # 先调用 DRF 默认处理器（它会填充 response.data）
    response = exception_handler(exc, context)

    if response is not None:
        # 统一错误格式
        error_code = getattr(exc, 'default_code', 'error')
        error_message = _extract_message(exc, response.data)

        response.data = {
            'code': error_code,
            'message': error_message,
            'detail': getattr(exc, 'detail', None),
        }

        # 附加字段（如果有的话）
        if hasattr(exc, 'extra_data'):
            response.data.update(exc.extra_data)

    return response


def _extract_message(exc, data):
    """从异常中提取友好提示"""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        # ValidationError: { field: [errors] }
        if 'detail' in data:
            return str(data['detail'])
        # DRF 格式错误：{ field_name: [msg1, msg2] }
        messages = []
        for field, errors in data.items():
            if isinstance(errors, list):
                msg = f"{field}: {', '.join(str(e) for e in errors)}"
            else:
                msg = f"{field}: {errors}"
            messages.append(msg)
        return '; '.join(messages) if messages else '请求参数错误'
    if isinstance(data, list):
        return '; '.join(str(item) for item in data)
    return str(data)


# ─────────────────────────────────────────────────────────────────
# 自定义业务异常（方便在业务代码中抛出）
# ─────────────────────────────────────────────────────────────────

class BusinessException(Exception):
    """业务异常基类"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'BUSINESS_ERROR'
    default_message = '业务处理失败'

    def __init__(self, message=None, code=None, status_code=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)


class ResourceNotFoundException(BusinessException):
    """资源不存在"""
    status_code = status.HTTP_404_NOT_FOUND
    default_code = 'NOT_FOUND'
    default_message = '请求的资源不存在'


class UnauthorizedException(BusinessException):
    """未授权"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = 'UNAUTHORIZED'
    default_message = '请先登录'


class ForbiddenException(BusinessException):
    """禁止访问"""
    status_code = status.HTTP_403_FORBIDDEN
    default_code = 'FORBIDDEN'
    default_message = '您没有权限执行此操作'


class ValidationException(BusinessException):
    """参数校验失败"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'VALIDATION_ERROR'
    default_message = '参数校验失败'
