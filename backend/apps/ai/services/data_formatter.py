"""Data sanitization — strip sensitive fields before sending to AI providers."""
import copy

# 敏感字段黑名单（任意嵌套层级都会被移除）
SENSITIVE_FIELDS = {
    'password', 'password_hash', 'token', 'secret',
    'session_key', 'session_data', 'api_key', 'apikey',
    'csrf_token', 'csrftoken', 'authorization',
    'private_key', 'access_token', 'refresh_token',
}


def sanitize_data(data):
    """递归移除敏感字段后返回新对象（不修改原始数据）.

    支持的输入类型: dict / list / tuple / 其他（原样返回）。
    """
    if isinstance(data, dict):
        return {
            k: sanitize_data(v)
            for k, v in data.items()
            if str(k).lower() not in SENSITIVE_FIELDS
        }
    if isinstance(data, list):
        return [sanitize_data(item) for item in data]
    if isinstance(data, tuple):
        return tuple(sanitize_data(item) for item in data)
    return data


def truncate_response(text: str, max_chars: int = 5000) -> str:
    """截断响应文本，防止单条记录过大."""
    if not text:
        return ''
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + '...[truncated]'


def mask_email(email: str) -> str:
    """脱敏邮箱（用于审计展示）."""
    if not email or '@' not in email:
        return email
    name, domain = email.split('@', 1)
    if len(name) <= 2:
        masked = name[0] + '*'
    else:
        masked = name[0] + '*' * (len(name) - 2) + name[-1]
    return f"{masked}@{domain}"


def clone_for_ai(data):
    """sanitize_data 的语义化别名（深拷贝保证不污染调用方）."""
    return copy.deepcopy(sanitize_data(data))
