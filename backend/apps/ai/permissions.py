"""AI permissions and stateful, revocable Agent credentials.

v2 tokens are deliberately incompatible with legacy stateless credentials.
Only a digest is persisted. Verification always consults the current database.
"""
import hashlib
import hmac
import re
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import DatabaseError
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from rest_framework.permissions import BasePermission


def _has_root_role(user) -> bool:
    """Re-read issuer state; session/permission object snapshots are not authority."""
    if not user or not getattr(user, 'pk', None) or not getattr(user, 'is_authenticated', False):
        return False
    from apps.rbac.models import User, UserRole
    current = User.objects.filter(pk=user.pk, is_active=True).first()
    if current is None:
        return False
    if current.is_superuser:
        return True
    return UserRole.objects.filter(user=current, role__code='root', role__is_deleted=False).exists()


class RootOnlyAI(BasePermission):
    message = '仅 root 角色可调用 AI 功能'

    def has_permission(self, request, view):
        return _has_root_role(request.user)


class RootOrAgentAuth(BasePermission):
    """A valid root session remains independent of the optional Agent header.

    Agents receive payload metadata only; they never become authenticated roots.
    DRF SessionAuthentication and its CSRF protection remain unchanged.
    """
    message = '需要 root 身份或有效的 Agent 授权 Token'

    def has_permission(self, request, view):
        if _has_root_role(request.user):
            return True
        token = request.headers.get('X-Agent-Token', '') or request.META.get('HTTP_X_AGENT_TOKEN', '')
        payload = AgentTokenService.verify(token)
        if payload is None:
            return False
        request._agent_payload = payload
        return True


class AgentTokenUnavailable(APIException):
    status_code = 503
    default_detail = 'Agent 授权服务不可用'
    default_code = 'agent_token_unavailable'


class AgentTokenService:
    """Database allowlist with random handles and an explicit dedicated secret.

    Revocation prevents subsequent verifications, not requests already authorized.
    Restoring issuer privileges can restore an unexpired, unrevoked credential.
    Explicit revocation is permanent. Database errors never fall back to HMAC-only.
    """
    _TOKEN = re.compile(r'v2\.([0-9a-f]{32})\.([0-9a-f]{64})', re.ASCII)

    @staticmethod
    def _secret() -> str | None:
        value = getattr(settings, 'AI_AGENT_TOKEN_SECRET', '')
        return value if isinstance(value, str) and len(value) >= 32 else None

    @classmethod
    def issue(cls, *, root_user_id: int, agent_id: str, ttl_hours: int = 24) -> str:
        from apps.ai.models import AgentCredential
        from apps.rbac.models import User
        secret = cls._secret()
        if secret is None:
            raise AgentTokenUnavailable()
        if (not isinstance(agent_id, str) or not agent_id.strip() or len(agent_id) > 100
                or isinstance(ttl_hours, bool) or not isinstance(ttl_hours, int) or not 1 <= ttl_hours <= 720):
            raise ValidationError('无效的 Agent ID 或授权时长')
        issuer = User.objects.filter(pk=root_user_id).first()
        if not _has_root_role(issuer):
            raise PermissionDenied('需要有效的 root 签发人')
        token_id = uuid.uuid4()
        body = f'v2.{token_id.hex}'
        signature = hmac.new(secret.encode(), body.encode('ascii'), hashlib.sha256).hexdigest()
        token = f'{body}.{signature}'
        AgentCredential.objects.create(
            id=token_id, issuer=issuer, agent_id=agent_id,
            token_digest=hashlib.sha256(token.encode('ascii')).hexdigest(),
            expires_at=timezone.now() + timedelta(hours=ttl_hours),
        )
        return token

    @classmethod
    def verify(cls, token: str) -> dict | None:
        from apps.ai.models import AgentCredential
        secret = cls._secret()
        if secret is None or not isinstance(token, str) or len(token) > 100:
            return None
        match = cls._TOKEN.fullmatch(token)
        if match is None:
            return None
        handle, signature = match.groups()
        expected = hmac.new(secret.encode(), f'v2.{handle}'.encode('ascii'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return None
        try:
            credential = AgentCredential.objects.select_related('issuer').filter(
                id=uuid.UUID(hex=handle),
                token_digest=hashlib.sha256(token.encode('ascii')).hexdigest(),
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
            ).first()
            if credential is None or not _has_root_role(credential.issuer):
                return None
        except DatabaseError:
            return None
        return {'exp': int(credential.expires_at.timestamp()), 'root_user_id': credential.issuer_id,
                'agent_id': credential.agent_id, 'token_id': str(credential.id)}

    @classmethod
    def revoke(cls, *, token_id, actor) -> None:
        """Any currently valid root can revoke; unknown/already revoked is idempotent.

        This standalone UPDATE commits before an autocommit API response. There
        is no soft-delete manager, and no code path clears revoked_at.
        """
        from apps.ai.models import AgentCredential
        if not _has_root_role(actor):
            raise PermissionDenied('需要有效的 root 身份')
        AgentCredential.objects.filter(pk=token_id, revoked_at__isnull=True).update(revoked_at=timezone.now())
