"""Synthetic integration bootstrap, not a production account installer."""
import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'));os.environ['DJANGO_SETTINGS_MODULE']='config.settings.integration'
import django;django.setup()
from django.core.management import call_command
from apps.rbac.models import User,Role,UserRole,RolePermission
call_command('migrate',verbosity=0,interactive=False)
password=os.environ['RAM_TEST_PASSWORD']
roles={code:Role.objects.create(name=code,code=code,is_unique=code=='boss') for code in ('root','boss','user','audit_reader')}
RolePermission.objects.create(role=roles['audit_reader'],permission_code='audit.read')
for i in range(22):User.objects.create_user(f'page-fixture-{i:02}',f'page{i}@example.invalid',None)
for name,role,superuser in [('e2e-root',None,True),('e2e-boss','boss',False),('e2e-user','user',False),('e2e-auditor','audit_reader',False)]:
 user=User.objects.create_user(name,name+'@example.invalid',password,is_superuser=superuser)
 if role:UserRole.objects.create(user=user,role=roles[role])

print('isolated synthetic fixtures initialized; no credential output')
