"""Original 27 BOSS regression assertions, preserved against the new source.
Source: 2026-11-17 verify_security.py patched branch; path/output/setup only adapted.
"""
import argparse,json,os,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'backend'));os.environ['DJANGO_SETTINGS_MODULE']='config.settings.test'
import django
from django.conf import settings
with tempfile.TemporaryDirectory(prefix='ram-boss-regression-') as tmp:
 settings.DATABASES['default']['NAME']=str(Path(tmp)/'test.sqlite3');django.setup()
 from django.core.management import call_command
 from rest_framework.test import APIClient
 from apps.rbac.models import User,Role,UserRole
 call_command('migrate',verbosity=0,interactive=False)
 roles={code:Role.objects.create(code=code,name=code,is_unique=code=='boss') for code in ['root','boss','user']}
 users={}
 for name,code,superuser in [('root','root',True),('root_role','root',False),('boss','boss',False),('peer_boss','boss',False),('ordinary','user',False)]:
  u=User.objects.create_user(username=name,email=name+'@example.invalid',password='Demo-Test-Only-739!',is_superuser=superuser);UserRole.objects.create(user=u,role=roles[code]);users[name]=u
 def client(name):
  c=APIClient(enforce_csrf_checks=True);c.get('/api/auth/csrf/');token=c.cookies['csrftoken'].value;res=c.post('/api/auth/login/',{'username':name,'password':'Demo-Test-Only-739!'},format='json',HTTP_X_CSRFTOKEN=token);assert res.status_code==200,('login',name,res.status_code);c.credentials(HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value);return c
 boss=client('boss');root=client('root');ordinary=client('ordinary');checks=[]
 def check(name,response,status):
  result={'name':name,'status':response.status_code,'expected':status,'pass':response.status_code==status};checks.append(result);assert result['pass'],result
 for target in ['root','root_role','boss','peer_boss']:
  uid=users[target].id
  check('BOSS reset '+target,boss.post(f'/api/rbac/users/{uid}/reset-password/',{'password':'Blocked-991!'},format='json'),403)
  check('BOSS update '+target,boss.put(f'/api/rbac/users/{uid}/',{'is_active':False},format='json'),403)
  check('BOSS delete '+target,boss.delete(f'/api/rbac/users/{uid}/'),403)
 check('BOSS self grant root',boss.put(f"/api/rbac/users/{users['ordinary'].id}/",{'role_ids':[roles['root'].id]},format='json'),403)
 check('BOSS create root account',boss.post('/api/rbac/users/',{'username':'new_root','email':'new@example.invalid','password':'Synthetic739!','role_ids':[roles['root'].id]},format='json'),403)
 check('BOSS edit root role',boss.put(f"/api/rbac/roles/{roles['root'].id}/",{'name':'Changed'},format='json'),403)
 check('BOSS create role',boss.post('/api/rbac/roles/',{'name':'new_role','code':'new_role'},format='json'),403)
 check('ordinary reset root',ordinary.post(f"/api/rbac/users/{users['root'].id}/reset-password/",{'password':'Blocked739!'},format='json'),403)
 check('root reset ordinary',root.post(f"/api/rbac/users/{users['ordinary'].id}/reset-password/",{'password':'Changed-Only-Test-739!'},format='json'),200)
 check('root edit ordinary',root.put(f"/api/rbac/users/{users['ordinary'].id}/",{'is_active':True},format='json'),200)
 check('BOSS edit ordinary',boss.put(f"/api/rbac/users/{users['ordinary'].id}/",{'is_active':True,'role_ids':[roles['user'].id]},format='json'),200)
 check('root create custom role',root.post('/api/rbac/roles/',{'name':'custom','code':'custom'},format='json'),201)
 for name in ['root','root_role','boss','peer_boss']:
  u=User.objects.get(id=users[name].id);assert u.check_password('Demo-Test-Only-739!') and u.is_active;checks.append({'name':'protected identity unchanged '+name,'pass':True})
 check('unauthenticated users list',APIClient().get('/api/rbac/users/'),403)
 audit_response=root.get('/api/audit/logs/')
 check('implemented audit API root read',audit_response,200)
 assert set(audit_response.data)=={'data','pagination'}
 assert all(set(row)=={'id','actor_id','actor_name','action','resource','object_id','outcome','created_at'} for row in audit_response.data['data'])
 check('ordinary audit denied',ordinary.get('/api/audit/logs/'),403)
 output={'mode':'new-prerelease-preserved-regression','checks':checks,'check_count':len(checks),'pass':all(x['pass'] for x in checks),'temporary_database':True,'model_network_calls':0}
 Path(a.output).write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(output,ensure_ascii=False,indent=2))
 from django.db import connections
 connections.close_all()
