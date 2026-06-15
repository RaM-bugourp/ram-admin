"""AI-specific exceptions."""
from apps.common.exceptions import BusinessError


class AIError(BusinessError):
    """AI 服务基础错误."""

    def __init__(self, message: str, code: str = 'AI_ERROR', status: int = 500):
        super().__init__(message=message, code=code, status=status)


class AIAllProvidersFailedError(AIError):
    """所有 Provider 均失败."""

    def __init__(self, message: str = '所有 AI Provider 均不可用'):
        super().__init__(message=message, code='AI_ALL_PROVIDERS_FAILED', status=503)


class AIProviderError(AIError):
    """单个 Provider 调用失败的内部错误（不直接返回给用户）."""

    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(message=message, code='AI_PROVIDER_ERROR', status=502)


class AIApprovalError(AIError):
    """审批流错误."""

    def __init__(self, message: str, code: str = 'AI_APPROVAL_ERROR', status: int = 400):
        super().__init__(message=message, code=code, status=status)


class AIRateLimitError(AIError):
    """调用频次超限."""

    def __init__(self, message: str = 'AI 调用频次已达上限'):
        super().__init__(message=message, code='AI_RATE_LIMIT_EXCEEDED', status=429)
