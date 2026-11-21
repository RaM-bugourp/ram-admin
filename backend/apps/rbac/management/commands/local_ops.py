"""Operator CLI, inherits OS access. Not an HTTP capability or root-password bypass."""
import json
from django.core.management.base import BaseCommand, CommandError
from apps.common import sqlite_ops

class Command(BaseCommand):
    help='Local private SQLite health, consistent backup, and isolated restore verification'
    def add_arguments(self,parser):
        parser.add_argument('operation',choices=['health','backup','restore'])
        parser.add_argument('--backup-id')
    def handle(self,*args,**options):
        try:
            op=options['operation']
            if op=='health':result=sqlite_ops.health()
            elif op=='backup':result=sqlite_ops.backup()
            else:result=sqlite_ops.restore(options['backup_id'])
        except sqlite_ops.OpsError as error:
            raise CommandError(error.code) from None
        except Exception:
            raise CommandError('LOCAL_OPS_FAILED') from None
        self.stdout.write(json.dumps(result,ensure_ascii=False))
        if not result.get('ok'):raise CommandError(result.get('code','HEALTH_FAILED'))
