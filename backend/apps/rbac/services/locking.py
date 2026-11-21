"""SQLite write reservation for core lifecycle transactions.

Called as the FIRST database statement inside @atomic, before permission/occupancy reads.
SQLite ignores select_for_update; a no-op UPDATE reserves its single writer instead.
No actor trust or authorization is supplied by this lock.
"""
from django.db import connection

def reserve_lifecycle_write():
    if not connection.in_atomic_block:raise RuntimeError('Lifecycle lock requires atomic transaction')
    if connection.vendor=='sqlite':
        from django.db import OperationalError
        from apps.common.exceptions import BusinessError
        try:
            with connection.cursor() as cursor:
                cursor.execute('UPDATE rbac_users SET updated_at = updated_at WHERE id = (SELECT MIN(id) FROM rbac_users)')
        except OperationalError as error:
            if 'locked' in str(error).lower():
                raise BusinessError('并发管理操作冲突，请重试', 'CONCURRENT_CONFLICT', 409) from error
            raise
