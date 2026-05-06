"""
任务调度模块
══════════════════════════════════════════════════════════════════

基于 APScheduler 的定时任务管理。

面试要点：

Q: APScheduler 和 Celery 的区别？
A:
    APScheduler：单机调度，适合轻量定时任务（每天跑一次统计等）
    Celery：分布式队列，支持异步任务+定时任务，适合大规模系统

    本框架选择 APScheduler 的原因：
        —— 单机足够满足大多数 admin 场景
        —— 无需额外依赖（Redis/RabbitMQ）
        —— 简单任务（统计报表、定期清理）用 APScheduler 更轻量

Q: APScheduler 的三种触发器？
A:
    date：一次性任务，在指定时间执行
    interval：间隔任务，每隔 N 秒/分钟/小时执行
    cron：Crontab 表达式，复杂定时规则（如每周一 9:00）

Q: Django 中使用 APScheduler 的注意点？
A:
    —— APScheduler 独立于 Django 运行，不走 Django 的 ORM 连接池
    —— 需要在 Django settings 里配置，避免连接泄漏
    —— 建议用 Django 的 on_startup 信号启动调度器
"""

from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# 全局调度器实例
_scheduler = None


def get_scheduler():
    """
    获取全局调度器实例（单例）。

    使用单例的原因：
        —— 应用启动时创建一次，整个进程生命周期复用
        —— 避免重复创建多个调度器冲突
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(
            timezone=timezone.get_current_timezone(),
            job_defaults={
                'coalesce': True,   # 积压的任务只执行一次（不重复补执行）
                'max_instances': 1, # 同一任务同时只能有一个实例在跑
                'misfire_grace_time': 60,  # 任务错过调度后60秒内仍可执行
            }
        )
    return _scheduler


def start_scheduler():
    """启动调度器（在 Django 启动信号中调用）"""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info('[Scheduler] 任务调度器已启动')


def stop_scheduler():
    """停止调度器（在 Django 关闭信号中调用）"""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info('[Scheduler] 任务调度器已停止')


# ─────────────────────────────────────────────────────────────────
# 常用调度装饰器
# ─────────────────────────────────────────────────────────────────

def cron_task(cron_expr=None, hour=None, minute=None, day=None, week=None, month=None):
    """
    Cron 定时任务装饰器。

    用法：
        @cron_task(hour=9, minute=30)  # 每天 9:30 执行
        def daily_report():
            print('生成日报')

        @cron_task(cron_expr='0 9 * * 1-5')  # 工作日 9:00 执行
        def weekday_morning():
            print('工作日早安任务')

    APScheduler cron 字段（与 Linux crontab 一致）：
        *    *    *    *    *
        分   时   日   月   周

        * = 任意值
        */5 = 每5个单位
        1-3 = 范围
        1,3 = 列表
    """
    def decorator(func):
        scheduler = get_scheduler()

        # cron 表达式优先
        trigger_kwargs = {}
        if cron_expr:
            trigger_kwargs['cron'] = {'expression': cron_expr}
        else:
            trigger_kwargs['cron'] = {
                'hour': hour, 'minute': minute,
                'day': day, 'month': month, 'week': week,
            }

        scheduler.add_job(
            func,
            trigger='cron',
            **trigger_kwargs,
            id=func.__name__,
            replace_existing=True,
            misfire_grace_time=60,
        )
        logger.info(f'[Scheduler] 注册定时任务: {func.__name__}')
        return func
    return decorator


def interval_task(minutes=None, seconds=None, hours=None):
    """
    间隔执行任务装饰器。

    用法：
        @interval_task(minutes=30)  # 每30分钟执行
        def sync_data():
            print('同步数据')

    """
    def decorator(func):
        scheduler = get_scheduler()
        scheduler.add_job(
            func,
            trigger='interval',
            minutes=minutes, seconds=seconds, hours=hours,
            id=func.__name__,
            replace_existing=True,
            misfire_grace_time=60,
        )
        logger.info(f'[Scheduler] 注册间隔任务: {func.__name__}')
        return func
    return decorator
