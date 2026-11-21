"""Real SQLite historical migration and actual production settings subprocess checks."""
import argparse,json,os,sys,tempfile,subprocess,secrets
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();checks=[]
 def check(name,value):assert value,name;checks.append({'name':name,'status':'pass'})
 sys.path.insert(0,str(ROOT/'backend'));os.environ['DJANGO_SETTINGS_MODULE']='config.settings.test'
 from django.conf import settings
 with tempfile.TemporaryDirectory(prefix='core-migration-') as tmp:
  settings.DATABASES['default']['NAME']=str(Path(tmp)/'isolated.sqlite3')
  import django;django.setup()
  from django.db import connection,connections
  from django.db.migrations.executor import MigrationExecutor
  try:
   old=[('ai','0002_agent_credentials'),('rbac','0003_add_role_is_unique_and_permission')]
   executor=MigrationExecutor(connection);executor.migrate(old);apps=executor.loader.project_state(old).apps
   User=apps.get_model('rbac','User');Approval=apps.get_model('ai','AIApproval');Call=apps.get_model('ai','AICallLog')
   user=User.objects.create(username='historical-only',email='historical@core.invalid',password_hash='!',is_superuser=True)
   ids=[]
   for status in ['pending','approved','rejected','executed','failed']:
    row=Approval.objects.create(agent_id='legacy',operation='create_user',params={'username':'historical-new','email':'new@core.invalid','password':'Historical-Secret-987!','password_hash':'injected','password_digest':'injected'},status=status,execution_error='Historical-Secret-987!');ids.append(row.pk)
   Call.objects.create(call_type='agent_submission',prompt='Historical-Secret-987!',response='Historical-Secret-987!')
   target=MigrationExecutor(connection).loader.graph.leaf_nodes();executor=MigrationExecutor(connection);executor.migrate(target);apps=executor.loader.project_state(target).apps
   Approval=apps.get_model('ai','AIApproval');rows=list(Approval.objects.order_by('id'));from django.contrib.auth.hashers import check_password
   check('all historical approvals preserved',len(rows)==5 and [x.pk for x in rows]==ids)
   check('historical issuer unknown not fabricated',all(x.submitted_by_id is None for x in rows))
   check('legacy pending hash consumes original password',check_password('Historical-Secret-987!',rows[0].params['password_digest']))
   check('terminal legacy passwords removed',all('password_digest' not in x.params for x in rows[1:]))
   check('legacy plaintext removed from rows','Historical-Secret-987!' not in str(list(Approval.objects.values())))
   check('legacy audit payload removed','Historical-Secret-987!' not in str(list(apps.get_model('ai','AICallLog').objects.values())))
   executor=MigrationExecutor(connection);executor.migrate(target);check('new migrations repeat safely',Approval.objects.count()==5)
   from apps.ai.services.ai_approval import AIApprovalService
   from apps.rbac.models import User as CurrentUser
   from django.test import override_settings
   with override_settings(AI_APPROVAL_AUTO_EXECUTE=True):result=AIApprovalService().review(approval_id=ids[0],root_user=CurrentUser.objects.get(pk=user.pk),action='approve')
   check('legacy pending executes without double hash',result.status=='executed' and CurrentUser.objects.get(username='historical-new').check_password('Historical-Secret-987!'))
   check('native ledger includes attribution migration',connection.cursor().execute("select count(*) from django_migrations where app='ai' and name='0003_aiapproval_submitted_by'").fetchone()[0]==1)
  finally:connections.close_all()
 env=os.environ.copy()
 for key in list(env):
  if key.startswith(('DJANGO_','AI_','OPENAI_','DEEPSEEK_','QCLAW_')):env.pop(key)
 code="import os,sys;sys.path.insert(0,'backend');os.environ['DJANGO_SETTINGS_MODULE']='config.settings.production';import django;django.setup();from django.conf import settings;assert not settings.DEBUG and settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE and settings.SECURE_SSL_REDIRECT;print('production config validated, no database opened')"
 for name,values,expected in [('missing secret',{},False),('weak secret',{'DJANGO_SECRET_KEY':'x'*60},False),('missing hosts',{'DJANGO_SECRET_KEY':secrets.token_urlsafe(48)},False),('wildcard hosts',{'DJANGO_SECRET_KEY':secrets.token_urlsafe(48),'DJANGO_ALLOWED_HOSTS':'*'},False),('missing database',{'DJANGO_SECRET_KEY':secrets.token_urlsafe(48),'DJANGO_ALLOWED_HOSTS':'admin.example.invalid'},False),('explicit valid',{'DJANGO_SECRET_KEY':secrets.token_urlsafe(48),'DJANGO_ALLOWED_HOSTS':'admin.example.invalid','DJANGO_DB_PATH':str(ROOT/'.tmp'/'production-not-opened.sqlite3')},True)]:
  result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env={**env,**values},capture_output=True,text=True,encoding='utf-8')
  check('production '+name,(result.returncode==0)==expected)
 output={'status':'pass','check_count':len(checks),'checks':checks,'limitations':['Only isolated SQLite/local production configuration import; no deployment/recovery acceptance.','Legacy password sanitization is deliberately one-way; no claim that historical plaintext never existed.']}
 Path(a.output).write_text(json.dumps(output,indent=2),encoding='utf-8');print(json.dumps(output,indent=2))
if __name__=='__main__':main()
