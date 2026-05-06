from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    sort = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'article_category'
        verbose_name = 'Article Category'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return self.name


class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    tags = models.CharField(max_length=200, blank=True, default='')
    view_count = models.IntegerField(default=0)

    # Audit fields
    created_by = models.ForeignKey(
        'user.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_articles',
    )
    updated_by = models.ForeignKey(
        'user.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='updated_articles',
    )
    owner_organization = models.ForeignKey(
        'rbac.Organization', on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    remark = models.CharField(max_length=255, blank=True, default='')

    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'article'
        verbose_name = 'Article'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = models.functions.Now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
