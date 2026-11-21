"""Fresh synthetic SQLite WAL backup, isolated restore, every-column and auth validation."""
from contextlib import closing
import argparse,datetime as dt,os,sys,secrets,json,subprocess,sqlite3,shutil,hashlib,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def cleanup_links(paths,private):
    for path in reversed(paths):
        assert path.parent==private/'backups' or path.parent.parent==ROOT/'.tmp'
        if os.path.lexists(path):
            attrs=path.lstat()
            assert path.is_symlink() or getattr(attrs,'st_file_attributes',0)&0x400
            os.rmdir(path)  # remove the junction itself, never recurse/follow target

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    run='ops-'+dt.datetime.now().strftime('%Y%m%dT%H%M%S')+'-'+secrets.token_hex(3);temp=ROOT/'.tmp'/run;temp.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy()
    for key in list(env):
        if key.startswith(('AI_','DJANGO_','RAM_TEST_')):env.pop(key)
    env.update(PYTHONUTF8='1',RAM_TEST_DB=str(temp/'source.sqlite3'),RAM_TEST_SECRET=secrets.token_urlsafe(48),RAM_TEST_AGENT_SECRET=secrets.token_urlsafe(48),RAM_TEST_PASSWORD=secrets.token_urlsafe(24),TEMP=str(temp),TMP=str(temp),TMPDIR=str(temp))
    os.environ.update(env);sys.path.insert(0,str(ROOT/'backend'));os.environ['DJANGO_SETTINGS_MODULE']='config.settings.integration'
    import django;django.setup()
    from django.core.management import call_command
    from django.db import connection
    from rest_framework.test import APIClient
    from apps.rbac.models import User,Role,UserRole,RolePermission
    from apps.ai.models import AIApproval,AIApprovalLog,AICallLog,Notification
    from apps.ai.permissions import AgentTokenService
    from apps.audit.models import OperationLog
    from apps.rbac import security
    from apps.common import sqlite_ops as ops
    report={'status':'running','checks':[],'target':'fresh-isolated-local-SQLite-WAL','production_recovery':False};created=[];links=[];link=None
    def check(name,yes):
        if not yes:raise AssertionError(name)
        report['checks'].append({'name':name,'passed':True})
    def reject(name,fn,code=None):
        try:fn()
        except ops.OpsError as e:check(name,code is None or e.code==code)
        else:raise AssertionError(name+' did not reject')
    try:
        call_command('migrate',verbosity=0,interactive=False)
        root=User.objects.create_user('ops-root','root@ops.invalid',env['RAM_TEST_PASSWORD'],is_superuser=True)
        role=Role.objects.create(name='Ops reader',code='ops_reader');reader=User.objects.create_user('ops-reader','reader@ops.invalid',None);UserRole.objects.create(user=reader,role=role);RolePermission.objects.create(role=role,permission_code='audit.read')
        approval=AIApproval.objects.create(agent_id='ops',operation='update_user',params={'user_id':reader.pk,'email':'new@ops.invalid'},reason='synthetic',submitted_by=root)
        AIApprovalLog.objects.create(approval=approval,root_user=root,action='submit');AICallLog.objects.create(root_user=root,call_type='synthetic',prompt='safe-synthetic');Notification.objects.create(recipient=root,title='Synthetic',message='Restore comparison')
        token=AgentTokenService.issue(root_user_id=root.pk,agent_id='ops-agent',ttl_hours=1)
        c=APIClient();c.force_login(root,backend='apps.rbac.backends.UserBackend');security.list_sessions(root,c.cookies['sessionid'].value);security.reserve_login('ops-account','127.0.0.25');OperationLog.objects.create(actor=root,action='ops.fixture',resource='audit')
        # Sentinel data would be damaged by accidentally running legacy data migrations
        # against default. Compare every table/column, not just one password marker.
        from django.contrib.auth.hashers import make_password
        approval.operation='create_user';approval.params={'password_digest':make_password(env['RAM_TEST_PASSWORD']),'username':'pending-synthetic','email':'pending@ops.invalid'};approval.reason='preserve-current-reason';approval.approver_comment='preserve-current-comment';approval.save()
        AICallLog.objects.create(root_user=root,call_type='agent_submission',prompt='preserve-current-safe-marker')
        def all_rows():
            with closing(ops._connect_ro(Path(env['RAM_TEST_DB']))) as db:
                names=[x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
                return {name:db.execute('SELECT * FROM \"'+name.replace('\"','\"\"')+'\"').fetchall() for name in names}
        with connection.cursor() as cursor:cursor.execute('PRAGMA journal_mode=WAL');check('source WAL mode',cursor.fetchone()[0].lower()=='wal')
        source_before=all_rows();ops._expected_schema.cache_clear()
        check('health safe booleans current schema',ops.health()['ok'])
        check('health schema probe leaves every source column unchanged',all_rows()==source_before)
        ops._expected_schema.cache_clear()
        backup=ops.backup();identity=backup['backup_id'];created.extend([ops.PRIVATE/'backups'/identity,ops.PRIVATE/'restores'/identity]);check('SQLite online backup succeeded',backup['ok'])
        check('backup leaves every default source column unchanged',all_rows()==source_before)
        approval.refresh_from_db();check('pending password digest reason comment preserved internally',bool(approval.params.get('password_digest')) and approval.reason=='preserve-current-reason' and approval.approver_comment=='preserve-current-comment')
        folder=ops.PRIVATE/'backups'/identity;backup_file=folder/'database.sqlite3';before=hashlib.sha256(Path(env['RAM_TEST_DB']).read_bytes()).hexdigest()
        # A live write after snapshot must not mutate the saved restore point.
        root.email='after-snapshot@ops.invalid';root.save()
        restore_source_before=all_rows();ops._expected_schema.cache_clear()
        result=ops.restore(identity);check('restore complete all columns migration metadata',result['all_columns_equal'] and result['migration_metadata_equal']);check('not live replacement',result['not_live_replacement'])
        check('cold restore schema probe leaves all default columns unchanged',all_rows()==restore_source_before)
        restored=ops.PRIVATE/'restores'/identity/'database.sqlite3'
        with closing(ops._connect_ro(backup_file)) as source,closing(ops._connect_ro(restored)) as target:
            counts=ops.compare(source,target);check('all business and security tables populated',all(counts.get(t,0)>0 for t in ['rbac_users','rbac_roles','rbac_user_roles','rbac_role_permissions','rbac_managed_sessions','rbac_login_windows','django_session','django_migrations','ai_approvals','ai_approval_logs','ai_call_logs','ai_notifications','ai_agent_credentials','audit_operation_logs']))
            hashes_equal=source.execute('SELECT password_hash FROM rbac_users ORDER BY id').fetchall()==target.execute('SELECT password_hash FROM rbac_users ORDER BY id').fetchall();check('password hashes internally identical never output',hashes_equal)
        connection.close();old_name=connection.settings_dict['NAME'];connection.settings_dict['NAME']=str(restored)
        try:
            user=User.objects.get(pk=root.pk);check('restored password works internal only',user.check_password(env['RAM_TEST_PASSWORD']));check('snapshot predates later live write',user.email=='root@ops.invalid')
            check('restored retained session authenticates',c.get('/api/auth/user-info/').status_code==200)
            check('restored token authenticates with same process secret',AgentTokenService.verify(token)['agent_id']=='ops-agent')
            self_client=APIClient();self_client.force_authenticate(user);check('restored RBAC audit business API',self_client.get('/api/audit/logs/').status_code==200)
            response=self_client.post(f'/api/ai/approval/{approval.pk}/review/',{'action':'approve'},format='json')
            check('preserved pending digest executes only in isolated clone',response.status_code==200 and response.data['data']['status']=='executed' and User.objects.get(username='pending-synthetic').check_password(env['RAM_TEST_PASSWORD']))
        finally:connection.close();connection.settings_dict['NAME']=old_name
        check('live original not overwritten',User.objects.get(pk=root.pk).email=='after-snapshot@ops.invalid')
        reject('refuse existing restored target',lambda:ops.restore(identity),'RESTORE_TARGET_EXISTS')
        for bad in ['../bad','C:\\public\\bad',str(backup_file),'x'*32,None]:reject('reject invalid backup id '+str(type(bad).__name__),lambda bad=bad:ops.restore(bad),'INVALID_BACKUP_ID')
        reject('unknown backup refused',lambda:ops.restore(uuid.uuid4().hex),'BACKUP_UNAVAILABLE')
        # Corrupt a fresh backup fixture, retain original successful backup untouched until cleanup.
        extra=ops.backup()['backup_id'];extra_folder=ops.PRIVATE/'backups'/extra;created.append(extra_folder);(extra_folder/'database.sqlite3').write_bytes(b'not sqlite');reject('corrupt backup digest refused',lambda:ops.restore(extra),'BACKUP_DIGEST_MISMATCH')
        if os.name=='nt':
            proc=subprocess.run([str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'),'-NoProfile','-Command',"$a=Get-Acl -LiteralPath '"+str(folder)+"'; if(-not $a.AreAccessRulesProtected){exit 1}; foreach($r in $a.Access){if($r.IsInherited -or $r.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value -notin @((([System.Security.Principal.WindowsIdentity]::GetCurrent()).User.Value),'S-1-5-18','S-1-5-32-544','S-1-3-4')){exit 2}}"],capture_output=True,text=True);check('private backup ACL protected only local owner system admins',proc.returncode==0)
            link=ops.PRIVATE/'backups'/uuid.uuid4().hex
            result=subprocess.run(['cmd','/c','mklink','/J',str(link),str(folder)],capture_output=True);check('junction fixture created',result.returncode==0);links.append(link);reject('junction backup folder refused',lambda:ops.restore(link.name),'LINK_PATH_REJECTED')
        from unittest.mock import patch
        with patch.object(ops,'_private',side_effect=ops.OpsError('PRIVATE_ACL_UNAVAILABLE')):
            count_before=len(list((ops.PRIVATE/'backups').iterdir()))
            reject('ACL failure stops backup without sensitive output',ops.backup,'PRIVATE_ACL_UNAVAILABLE')
            check('ACL failure creates no backup data',len(list((ops.PRIVATE/'backups').iterdir()))==count_before)
        if os.name=='nt':
            for private_file in [folder/'database.sqlite3',folder/'manifest.json',restored]:
                escaped=str(private_file).replace("'","''")
                command="$a=Get-Acl -LiteralPath '"+escaped+"'; if(-not $a.AreAccessRulesProtected){exit 1};foreach($r in $a.Access){if($r.IsInherited -or $r.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value -notin @((([System.Security.Principal.WindowsIdentity]::GetCurrent()).User.Value),'S-1-5-18','S-1-5-32-544')){exit 2}}"
                result=subprocess.run([str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'),'-NoProfile','-Command',command],capture_output=True)
                check('private file DACL '+private_file.name,result.returncode==0)
            link=temp/'ancestor-junction';subprocess.run(['cmd','/c','mklink','/J',str(link),str(ops.PRIVATE)],capture_output=True,check=True);links.append(link)
            reject('ancestor junction path refused',lambda:ops._unlinked(link/'backups'/identity/'database.sqlite3'),'LINK_PATH_REJECTED')
            cleanup_links(links,ops.PRIVATE);check('all tracked junction fixtures removed',all(not os.path.lexists(p) for p in links));link=None
            exceptional=temp/'exception-junction';subprocess.run(['cmd','/c','mklink','/J',str(exceptional),str(ops.PRIVATE)],capture_output=True,check=True);links.append(exceptional)
            try:
                raise RuntimeError('synthetic cleanup branch')
            except RuntimeError:pass
            finally:cleanup_links([exceptional],ops.PRIVATE)
            check('junction finally cleanup on injected exception',not os.path.lexists(exceptional))
        for label,sql in [('table','DROP TABLE audit_operation_logs'),('column','ALTER TABLE ai_notifications DROP COLUMN title'),('index','DROP INDEX idx_user_email'),('unique','DROP INDEX rbac_user_roles_user_id_role_id_20a81ac2_uniq')]:
            broken=temp/('broken-'+label+'.sqlite3')
            with closing(ops._connect_ro(backup_file)) as src,closing(sqlite3.connect(broken)) as dst:
                src.backup(dst)
                if label=='unique':
                    index=next(x[1] for x in dst.execute("PRAGMA index_list('rbac_user_roles')") if x[2] and not x[1].startswith('sqlite_autoindex'))
                    sql='DROP INDEX \"'+index.replace('\"','\"\"')+'\"'
                dst.execute(sql);dst.commit()
            with closing(ops._connect_ro(broken)) as db:reject('schema '+label+' drift refused despite ledger',lambda:ops.structure(db),'SCHEMA_MISMATCH')
            broken_id=uuid.uuid4().hex;broken_folder=ops.PRIVATE/'backups'/broken_id;broken_folder.mkdir();ops._private(broken_folder,True);created.append(broken_folder)
            shutil.copyfile(broken,broken_folder/'database.sqlite3');ops._private(broken_folder/'database.sqlite3')
            (broken_folder/'manifest.json').write_text(json.dumps({'id':broken_id,'sha256':hashlib.sha256(broken.read_bytes()).hexdigest()}));ops._private(broken_folder/'manifest.json')
            reject('restore rejects '+label+' schema drift',lambda:ops.restore(broken_id),'SCHEMA_MISMATCH')
            check('invalid restore '+label+' creates no destination',not (ops.PRIVATE/'restores'/broken_id).exists())
            connection.close();connection.settings_dict['NAME']=str(broken)
            try:
                check('health rejects '+label+' drift',not ops.health()['ok'])
                reject('backup rejects '+label+' drift',ops.backup,'SCHEMA_MISMATCH')
            finally:connection.close();connection.settings_dict['NAME']=old_name
        check('all negative operations leave default source untouched',all_rows()==restore_source_before)
        from unittest.mock import patch
        ops._expected_schema.cache_clear()
        baseline_rows=all_rows()
        with patch.object(ops.subprocess,'run',return_value=subprocess.CompletedProcess([],1,stdout='',stderr='never expose this marker')):
            reject('reference child failure rejects schema',ops._expected_schema,'REFERENCE_SCHEMA_UNAVAILABLE')
        ops._expected_schema.cache_clear()
        check('reference child failure never writes configured database',all_rows()==baseline_rows)
        for label,kwargs in [('timeout',{'side_effect':subprocess.TimeoutExpired('safe-child',1)}),('launch',{'side_effect':OSError('sensitive path marker')}),('nonjson',{'return_value':subprocess.CompletedProcess([],0,stdout='bad json',stderr='')}),('shape',{'return_value':subprocess.CompletedProcess([],0,stdout='{}',stderr='')})]:
            ops._expected_schema.cache_clear()
            with patch.object(ops.subprocess,'run',**kwargs):reject('reference '+label+' failure closed',ops._expected_schema,'REFERENCE_SCHEMA_UNAVAILABLE')
            check('reference '+label+' leaves every default row unchanged',all_rows()==baseline_rows)
        ops._expected_schema.cache_clear()
        report['status']='pass';report['table_count']=len(counts);report['check_count']=len(report['checks'])
    finally:
        connection.close()
        cleanup_links(links,ops.PRIVATE)
        for folder in reversed(created):
            assert folder.parent in [ops.PRIVATE/'backups',ops.PRIVATE/'restores'] and ops.ID.fullmatch(folder.name)
            if folder.exists():shutil.rmtree(folder)
        shutil.rmtree(temp);report['cleanup']={'synthetic_database_removed':not temp.exists(),'created_private_folders_removed':all(not f.exists() for f in created),'all_tracked_links_removed':all(not os.path.lexists(p) for p in links),'services_started':False}
        Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'check_count':report['check_count'],'table_count':report['table_count']}))
if __name__=='__main__':main()
