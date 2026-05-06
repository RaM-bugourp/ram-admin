"""
基础模型层
══════════════════════════════════════════════════════════════════

本模块提供 3 个抽象基类，业务模型通过继承获得对应能力：

    class Product(SoftDeleteMixin, models.Model):
        # 自动获得：软删除 + 查询时排除已删记录
        ...

    class Article(BaseAuditModel, models.Model):
        # 自动获得：审计字段 + owner_organization + 软删除
        name = models.CharField(max_length=100)
        ...

    class BookViewSet(AuditOwnerPopulateMixin, ModelViewSet):
        # perform_create 时自动填充 created_by / owner_organization
        # perform_update 时自动更新 updated_by
        ...

══════════════════════════════════════════════════════════════════

为什么要用 Mixin 而不是直接继承？
─────────────────────────────────────
1. Python 单继承限制多，Mixin 可以叠加使用
2. 字段逻辑（模型层）和业务逻辑（视图层）分离
3. 一个 ViewSet 可以同时用 AuditOwnerPopulateMixin + SoftDeleteMixin
"""

from django.db import models
from django.conf import settings


class SoftDeleteMixin(models.Model):
    """
    软删除混入 —— 给模型添加软删除能力。

    使用方式：
        class Article(SoftDeleteMixin, models.Model):
            title = models.CharField(max_length=200)

    效果：
        Article.objects.all()          → 自动过滤 is_deleted=False
        article.delete()               → 改为 is_deleted=True（不真实删除）
        Article.all_objects.all()      → 包含已删除记录（慎用）
        Article.restore(article.pk)   → 恢复已删除记录

    原理：
        在 QuerySet 层面过滤已删除记录，而不是在数据库加约束。
        这样已有数据不会物理删除，可追溯、可恢复。
    """

    is_deleted = models.BooleanField(default=False, verbose_name='已删除')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='删除时间')

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """
        重写 delete() 行为：
        调用 .delete() 时改为软删除（设置 is_deleted=True）
        而不是物理删除数据。

        这是 Django 的约定 —— 重写 delete() 改变删除行为。
        """
        # 标记为已删除，不真实删除
        self.is_deleted = True
        self.deleted_at = self._now()
        self.save(using=using, update_fields=['is_deleted', 'deleted_at'])

    @staticmethod
    def _now():
        """获取当前时间（Django timezone aware）"""
        from django.utils import timezone
        return timezone.now()

    def restore(self):
        """
        恢复已删除的记录。

        用法：
            Article.restore(article_pk)
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class BaseAuditModel(SoftDeleteMixin):
    """
    审计与归属字段抽象基类。

    继承此基类的模型，自动获得以下字段：
        created_at / updated_at     —— 时间戳
        created_by / updated_by     —— 用户（外键，SET_NULL 保护）
        owner_organization         —— 归属组织（数据隔离用）
        remark                      —— 备注

    为什么需要 created_by / updated_by？
        —— 记录是谁创建/修改的，方便审计
        —— 配合数据权限，限制用户只能操作自己的数据

    为什么需要 owner_organization？
        —— 企业场景下，按部门/子公司做数据隔离
        —— 一个用户属于某个组织，只能看该组织的数据
    """

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_created_by',  # 动态关联名
        verbose_name='创建人',
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_updated_by',
        verbose_name='更新人',
    )

    owner_organization = models.ForeignKey(
        'rbac.Organization',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_owned',
        verbose_name='归属组织',
    )

    remark = models.CharField(max_length=500, blank=True, default='', verbose_name='备注')

    class Meta(SoftDeleteMixin.Meta):
        abstract = True
        indexes = [
            # 为常用查询字段加索引
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['owner_organization']),
            # 联合索引：常见查询模式
            models.Index(fields=['owner_organization', 'is_deleted']),
        ]
