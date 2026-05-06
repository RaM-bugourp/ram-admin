"""
Core Foundation 模块 —— 零业务依赖的基础设施

本包提供的所有组件都不含业务逻辑，可直接在任何 Django 项目中使用。

导出清单：
    from ram_core.foundation.models import BaseAuditModel, SoftDeleteMixin
    from ram_core.foundation.mixins import (
        AuditOwnerPopulateMixin,
        SoftDeleteMixin,
        ActionSerializerMixin,
    )
    from ram_core.foundation.pagination import StandardPagination

使用示例（完整用法）：
    # models.py
    class Article(BaseAuditModel, models.Model):
        title = models.CharField(max_length=200)
        content = models.TextField()
        category = models.ForeignKey('Category', on_delete=models.CASCADE)

    # views.py
    class ArticleViewSet(
        AuditOwnerPopulateMixin,
        SoftDeleteMixin,
        ActionSerializerMixin,
        ModelViewSet
    ):
        queryset = Article.objects.all()
        serializer_class = ArticleSerializer
        list_serializer_class = ArticleListSerializer
        filterset_fields = ['category', 'created_by']
        search_fields = ['title', 'content']
        ordering_fields = ['created_at', 'updated_at']
        permission_classes = [RBACPermission]
        required_permissions = ['article:list', 'article:create']
"""

from .models import BaseAuditModel, SoftDeleteMixin
from .mixins import (
    AuditOwnerPopulateMixin,
    SoftDeleteMixin as ViewSetSoftDeleteMixin,
    ActionSerializerMixin,
)
from .pagination import StandardPagination

__all__ = [
    # models
    'BaseAuditModel',
    'SoftDeleteMixin',
    # mixins
    'AuditOwnerPopulateMixin',
    'ActionSerializerMixin',
    # pagination
    'StandardPagination',
]
