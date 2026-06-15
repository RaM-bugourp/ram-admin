"""AI permissions — root-only access + agent token verification."""
import hashlib
import hmac
import json
import time

from django.conf import settings
from rest_framework.permissions import BasePermission


def _has_root_role(user) -> bool:
    """检查用户是否持有 root 角色."""
    if not user or not user.id or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    from apps.rbac.models import UserRole
    return UserRole.objects.filter(user=user, role__code='root').exists()


class RootOnlyAI(BasePermission):
    """只有 root 角色可以调用 AI 接口."""

    message = '仅 root 角色可调用 AI 功能'

    def has_permission(self, request, view):
        return _has_root_role(request.user)


class RootOrAgentAuth(BasePermission):
    """允许 root 直接访问，或 Agent 携带有效 root 签发的 Token 访问.

    Token 格式: <exp_timestamp>.<root_user_id>.<signature>
    signature = HMAC-SHA256(secret, f"{exp}.{root_user_id}")
    """

    message = '需要 root 身份或有效的 Agent 授权 Token'

    def has_permission(self, request, view):
        # 1) root 直接放行
        if _has_root_role(request.user):
            return True

        # 2) 检查 Agent Token
        token = request.headers.get('X-Agent-Token', '') or request.META.get('HTTP_X_AGENT_TOKEN', '')
        if not token:
            return False

        payload = AgentTokenService.verify(token)
        if payload is None:
            return False

        # 把解析出的 Agent 身份挂到 request 上，供 view 使用
        request._agent_payload = payload
        return True


class AgentTokenService:
    """Agent Token 签发与验证（HMAC，无状态）."""

    @staticmethod
    def _secret() -> str:
        return getattr(settings, 'AI_AGENT_TOKEN_SECRET', '') or 'insecure-default'

    @classmethod
    def issue(cls, *, root_user_id: int, agent_id: str, ttl_hours: int = 24) -> str:
        """root 为某个 Agent 签发 Token."""
        exp = int(time.time()) + ttl_hours * 3600
        body = f"{exp}.{root_user_id}.{agent_id}"
        sig = hmac.new(cls._secret().encode(), body.encode(), hashlib.sha256).hexdigest()
        return f"{body}.{sig}"

    @classmethod
    def verify(cls, token: str) -> dict | None:
        """验证 Token，成功返回 {exp, root_user_id, agent_id}，失败返回 None."""
        if not token or token.count('.') != 3:
            return None
        exp_str, root_id_str, agent_id, sig = token.split('.')
        try:
            exp = int(exp_str)
            root_user_id = int(root_id_str)
        except ValueError:
            return None

        body = f"{exp_str}.{root_id_str}.{agent_id}"
        expected = hmac.new(cls._secret().encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return None
        if exp < time.time():
            return None

        return {
            'exp': exp,
            'root_user_id': root_user_id,
            'agent_id': agent_id,
        }
