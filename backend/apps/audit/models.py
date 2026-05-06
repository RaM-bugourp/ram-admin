from django.db import models


class OperationLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        'user.User', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='User',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='other')
    resource_type = models.CharField(max_length=100, blank=True, default='')
    resource_id = models.CharField(max_length=50, blank=True, default='')
    description = models.TextField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, default='')
    request_data = models.JSONField(null=True, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_operation_log'
        verbose_name = 'Operation Log'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} {self.action} {self.resource_type}#{self.resource_id}'
