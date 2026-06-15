"""Management command — show AI provider pool status (for ops/debugging)."""
from django.core.management.base import BaseCommand

from apps.ai.services.ai_failover import CircuitBreakerRegistry, get_active_providers
from apps.ai.services.ai_service import get_ai_service


class Command(BaseCommand):
    help = '查看 AI Provider 池状态'

    def handle(self, *args, **options):
        service = get_ai_service()
        status = service.get_status()

        self.stdout.write(self.style.SQL_TABLE('═══ AI Provider 池状态 ═══'))
        self.stdout.write(f"当前 Provider: {status['current_provider']}")
        self.stdout.write(f"是否发生故障转移: {status['failover_triggered']}")
        self.stdout.write(f"Mock 模式: {status['mock_mode']}")
        self.stdout.write('')

        if not status['providers']:
            self.stdout.write(self.style.WARNING('  (无任何可用 Provider)'))
            return

        self.stdout.write(self.style.SQL_TABLE('Provider 列表:'))
        for p in status['providers']:
            state_color = {
                'healthy': self.style.SUCCESS,
                'degraded': self.style.WARNING,
                'failed': self.style.ERROR,
            }.get(p['status'], self.style.NOTICE)
            self.stdout.write(
                f"  • {p['name']:12s} model={p.get('model', ''):28s} "
                f"status={state_color(p['status'])} "
                f"failures={p.get('failures', 0)}"
            )
