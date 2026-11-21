"""Real isolated SQLite migration/restart checks; never loads project databases."""
import argparse, hashlib, json, os, sqlite3, subprocess, sys, tempfile
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--output',required=True); a=p.parse_args()
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'backend')); os.environ['DJANGO_SETTINGS_MODULE']='config.settings.test'
from django.conf import settings
with tempfile.TemporaryDirectory(prefix='ram-schema-') as tmp:
    db=Path(tmp)/'migration.sqlite3'
    settings.DATABASES['default']['NAME']=str(db)
    import django; django.setup()
    from django.core.management import call_command
    from django.db import connection, connections
    from django.db.migrations.executor import MigrationExecutor
    checks=[]
    def checked(name,condition):
        assert condition,name
        checks.append({'name':name,'status':'pass'})
    def migrate(target):
        executor=MigrationExecutor(connection)
        executor.migrate(target)
        return executor.loader.project_state(target).apps
    # Start at actual old ai schema and seed pre-existing approval/audit rows.
    old_targets=[('ai','0001_initial'),('rbac','0003_add_role_is_unique_and_permission')]
    apps=migrate(old_targets)
    User=apps.get_model('rbac','User'); Approval=apps.get_model('ai','AIApproval'); Log=apps.get_model('ai','AIApprovalLog')
    user=User.objects.create(username='migration-synthetic',email='migration@example.invalid',password_hash='unusable',is_active=True,is_superuser=True)
    approval=Approval.objects.create(agent_id='historical-agent',operation='create_user',params={'synthetic':True},reason='pre-existing',status='pending')
    Log.objects.create(approval=approval,root_user_id=user.pk,action='submit',comment='historical')
    expected=(approval.pk,approval.approval_uid,approval.params,approval.status)
    before=set(connection.introspection.table_names())
    new_targets=[('ai','0002_agent_credentials'),('rbac','0003_add_role_is_unique_and_permission')]
    apps=migrate(new_targets)
    checked('0001 upgrade creates registry', 'ai_agent_credentials' in connection.introspection.table_names())
    A=apps.get_model('ai','AIApproval'); row=A.objects.get(pk=approval.pk)
    checked('upgrade preserves approval payload identity status', (row.pk,row.approval_uid,row.params,row.status)==expected)
    checked('upgrade preserves historical approval audit',apps.get_model('ai','AIApprovalLog').objects.filter(approval_id=row.pk,comment='historical').count()==1)
    migrate(new_targets)
    checked('repeated migrate preserves existing business rows',A.objects.count()==1)
    from apps.ai.permissions import AgentTokenService
    from apps.ai.models import AgentCredential
    from apps.rbac.models import User as CurrentUser
    issuer=CurrentUser.objects.get(pk=user.pk)
    token=AgentTokenService.issue(root_user_id=issuer.pk,agent_id='persisted-agent')
    handle=AgentCredential.objects.get().pk
    def process_verify(expected):
        payload={'database':str(db),'secret':settings.AI_AGENT_TOKEN_SECRET,'token':token,'expected_accepted':expected}
        r=subprocess.run([sys.executable,str(root/'tools/credential_process_probe.py')],input=json.dumps(payload),capture_output=True,text=True)
        assert r.returncode==0, 'independent credential probe failed (output intentionally redacted)'
        return json.loads(r.stdout)['accepted']
    checked('full independent process accepts active registered credential',process_verify(True) is True)
    AgentTokenService.revoke(token_id=handle,actor=issuer)
    checked('full independent process rejects revoked credential',process_verify(False) is False)
    # Child gets only isolated temp DB and handle; no token/secret crosses process boundary.
    child='import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); r=c.execute("select revoked_at from ai_agent_credentials where id=?",(sys.argv[2],)).fetchone(); assert r and r[0]; print("revocation visible in independent process")'
    run=subprocess.run([sys.executable,'-c',child,str(db),handle.hex],capture_output=True,text=True)
    checked('committed revocation visible in independent process',run.returncode==0)
    connections.close_all()
    checked('revocation still denied after reconnect',AgentTokenService.verify(token) is None)
    # Real missing table failure must reject, not fall back to valid signature.
    migrate(old_targets)
    checked('reverse removes registry as documented','ai_agent_credentials' not in connection.introspection.table_names())
    checked('missing migration denies formerly signed token',AgentTokenService.verify(token) is None)
    apps=migrate(old_targets)
    row=apps.get_model('ai','AIApproval').objects.get(pk=approval.pk)
    checked('reverse preserves old business row',(row.pk,row.approval_uid,row.params,row.status)==expected)
    apps=migrate(new_targets)
    checked('reapply registry empty requires reissue',apps.get_model('ai','AgentCredential').objects.count()==0)
    checked('reapply never revives dropped old credential',AgentTokenService.verify(token) is None)
    ledger=list(connection.cursor().execute("select app,name from django_migrations where app in ('ai','rbac') order by app,name"))
    checked('native migration ledger contains 0002',('ai','0002_agent_credentials') in ledger)
    result={'status':'pass','target':{'engine':'SQLite','version':sqlite3.sqlite_version,'id':'isolated-temporary-migration-file'},'checks':checks,'check_count':len(checks),'ledger':ledger,'migration_sha256':hashlib.sha256((root/'backend/apps/ai/migrations/0002_agent_credentials.py').read_bytes()).hexdigest(),'limitations':['Reverse deliberately deletes credential registry; never approved for production rollback.','No production backup/restore, interrupted migration injection or multiworker in-flight cancellation claim.','Independent-process check reads committed revocation state; no concurrent stress benchmark.']}
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result,indent=2)); connections.close_all()
