"""Base model with timestamps and soft-delete."""
from django.db import models


class BaseModel(models.Model):
    """Abstract base model — created_at, updated_at, soft-delete."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_deleted = models.BooleanField(default=False, verbose_name="软删除")

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self):
        """Mark as deleted without removing the row."""
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])
