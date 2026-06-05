"""Django Manager that auto-filters soft-deleted records."""
from django.db import models


class BaseManager(models.Manager):
    """All queries exclude is_deleted=True by default."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def with_deleted(self):
        """Return all records including soft-deleted ones."""
        return super().get_queryset()
