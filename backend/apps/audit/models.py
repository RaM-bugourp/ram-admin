"""Minimal core audit. No free-form payloads, credentials, prompts, or tokens."""
from django.db import models

class OperationLog(models.Model):
    actor = models.ForeignKey('rbac.User',null=True,on_delete=models.SET_NULL,related_name='operation_logs')
    action = models.CharField(max_length=64)
    resource = models.CharField(max_length=32)
    object_id = models.CharField(max_length=64,blank=True)
    outcome = models.CharField(max_length=16,default='success')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table='audit_operation_logs'
        ordering=['-created_at','-id']
