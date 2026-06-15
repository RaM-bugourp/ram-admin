"""Management command — clean up old AI audit logs based on retention policy."""
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.ai.services.ai_audit import AIAuditService


class Command(BaseCommand):
    help = '清理超过保留期的 AI 调用审计日志'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help=f'保留天数（默认读取 AI_AUDIT_RETENTION_DAYS，当前={settings.AI_AUDIT_RETENTION_DAYS}）',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='只统计不删除',
        )

    def handle(self, *args, **options):
        days = options.get('days') or settings.AI_AUDIT_RETENTION_DAYS
        dry = options.get('dry_run')

        if days <= 0:
            self.stdout.write(self.style.WARNING(
                f'保留天数 = {days}（0 或负值表示永久保留），跳过清理。'
            ))
            return

        if dry:
            from datetime import timedelta
            from django.utils import timezone
            from apps.ai.models import AICallLog
            cutoff = timezone.now() - timedelta(days=days)
            count = AICallLog.objects.filter(created_at__lt=cutoff).count()
            self.stdout.write(f'[DRY RUN] 将删除 {count} 条早于 {days} 天的审计日志')
            return

        deleted = AIAuditService.cleanup_old_logs(retention_days=days)
        self.stdout.write(self.style.SUCCESS(
            f'已清理 {deleted} 条早于 {days} 天的 AI 审计日志'
        ))
