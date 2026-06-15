"""Notification service — in-app alerts to root users on provider failures."""
import logging

from django.conf import settings

from apps.ai.models import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """站内通知服务（主要供 AI Provider 告警使用）."""

    @staticmethod
    def _find_root_users():
        """查询所有持有 root 角色的用户."""
        from apps.rbac.models import User, UserRole
        return list(
            User.objects.filter(
                is_deleted=False, is_active=True,
                user_roles__role__code='root',
            ).distinct()
        )

    @classmethod
    def send(cls, *, user, title: str, message: str, level: str = 'info') -> Notification:
        """向单个用户发送通知."""
        return Notification.objects.create(
            recipient=user,
            title=title,
            message=message,
            level=level,
        )

    @classmethod
    def broadcast_to_roots(cls, *, title: str, message: str, level: str = 'warning') -> int:
        """向所有 root 用户群发通知，返回发送条数."""
        roots = cls._find_root_users()
        count = 0
        for root in roots:
            Notification.objects.create(
                recipient=root, title=title, message=message, level=level,
            )
            count += 1
        logger.info("Broadcast to %d root users: %s", count, title)
        return count

    @classmethod
    def alert_provider_failure(cls, provider_name: str, error: str) -> int:
        """Provider 故障告警."""
        # Webhook 告警（可选）
        cls._maybe_send_webhook(provider_name, error)

        return cls.broadcast_to_roots(
            title=f"⚠️ AI Provider 故障告警",
            message=(
                f"Provider '{provider_name}' 调用失败：\n{error}\n\n"
                "系统已自动切换到备用 Provider。"
            ),
            level='error',
        )

    @classmethod
    def _maybe_send_webhook(cls, provider_name: str, error: str) -> None:
        """可选：把告警推到钉钉/企业微信 Webhook."""
        webhook = getattr(settings, 'AI_FAILOVER_ALERT_WEBHOOK', '')
        channel = getattr(settings, 'AI_FAILOVER_ALERT_CHANNEL', 'notification')

        if channel != 'webhook' or not webhook:
            return

        import json
        import urllib.request
        import urllib.error

        payload = json.dumps({
            'msgtype': 'text',
            'text': {
                'content': f"[ram-adminx] AI Provider '{provider_name}' 故障: {error}",
            },
        }).encode('utf-8')

        try:
            req = urllib.request.Request(webhook, data=payload, method='POST')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
        except (urllib.error.URLError, Exception) as e:  # noqa: BLE001
            logger.warning("Webhook 告警发送失败: %s", e)
