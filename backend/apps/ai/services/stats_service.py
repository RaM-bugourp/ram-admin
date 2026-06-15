"""AI stats collector — gathers system data for analyze/report endpoints."""
from collections import Counter

from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from apps.rbac.models import User, Role, UserRole


def collect_dashboard_stats() -> dict:
    """采集仪表盘原始统计数据."""
    today = timezone.now()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    return {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'inactive_users': User.objects.filter(is_active=False).count(),
        'new_users_7d': User.objects.filter(created_at__gte=week_ago).count(),
        'new_users_30d': User.objects.filter(created_at__gte=month_ago).count(),
        'total_roles': Role.objects.count(),
        'total_assignments': UserRole.objects.count(),
    }


def collect_role_distribution() -> list[dict]:
    """角色分布统计."""
    qs = (
        UserRole.objects
        .values('role__code', 'role__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    return [
        {'code': item['role__code'], 'name': item['role__name'], 'count': item['count']}
        for item in qs
    ]


def collect_user_activity() -> dict:
    """用户活跃度（按注册日聚合最近 30 天）."""
    today = timezone.now()
    month_ago = today - timedelta(days=30)

    qs = User.objects.filter(created_at__gte=month_ago)
    daily = Counter()
    for u in qs:
        key = u.created_at.date().isoformat()
        daily[key] += 1

    return {
        'new_users_daily': dict(sorted(daily.items())),
        'no_login_users': User.objects.filter(
            is_active=True, last_login_at__isnull=True
        ).count(),
        'login_users': User.objects.filter(
            is_active=True, last_login_at__isnull=False
        ).count(),
    }


def collect_report_data(report_type: str) -> dict:
    """根据报告类型采集对应数据."""
    if report_type == 'user_activity':
        return {
            'stats': collect_dashboard_stats(),
            'activity': collect_user_activity(),
        }
    if report_type == 'role_distribution':
        return {
            'stats': collect_dashboard_stats(),
            'roles': collect_role_distribution(),
        }
    # system_overview
    return {
        'stats': collect_dashboard_stats(),
        'roles': collect_role_distribution(),
        'activity': collect_user_activity(),
    }
