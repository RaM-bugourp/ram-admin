"""Run real local checks; write immutable timestamped evidence, never production PASS."""
import argparse, datetime as dt, hashlib, json, os, platform, re, shutil, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'docs/harness/evidence'
EXCLUDE={'.git','node_modules','__pycache__','.venv','venv','dist','.npm-cache','.tmp','.private-ops'}
def sha(data): return hashlib.sha256(data).hexdigest()
def dump(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def inventory():
    rows=[]
    for base,dirs,files in os.walk(ROOT):
        dirs[:]=sorted(d for d in dirs if d not in EXCLUDE and (Path(base)/d)!=EVIDENCE)
        for name in sorted(files):
            p=Path(base)/name;rel=p.relative_to(ROOT).as_posix()
            if rel=='release-manifest.json' or name.endswith(('.pyc','.log')):continue
            rows.append({'path':rel,'sha256':sha(p.read_bytes()),'size':p.stat().st_size})
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--python',default=sys.executable);p.add_argument('--skip-install',action='store_true');p.add_argument('--run-id');p.add_argument('--browser-python',help='Run real HTTP+Edge using this Python with Playwright');a=p.parse_args()
    run_id=a.run_id or dt.datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%z')+'-'+os.urandom(3).hex()
    if not re.fullmatch(r'[A-Za-z0-9_+.-]+',run_id):raise ValueError('unsafe run id')
    out=EVIDENCE/run_id;out.mkdir(parents=True,exist_ok=False)
    if hasattr(sys.stdout, 'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    env=os.environ.copy();env['PYTHONUTF8']='1';env['npm_config_cache']=str(ROOT/'.npm-cache');env['npm_config_audit']='false';env['npm_config_fund']='false'
    temp_root=ROOT/'.tmp'/run_id;temp_root.mkdir(parents=True,exist_ok=False)
    env['TEMP']=str(temp_root);env['TMP']=str(temp_root);env['TMPDIR']=str(temp_root)
    def cleanup_temp():
        try:
            assert temp_root.parent == ROOT/'.tmp' and temp_root.name == run_id
            shutil.rmtree(temp_root)
            dump(out/'cleanup.json',{'temporary_directory':str(temp_root),'removed':not temp_root.exists(),'background_jobs_started':[]})
        except Exception as error:
            dump(out/'cleanup.json',{'temporary_directory':str(temp_root),'removed':False,'error_type':type(error).__name__,'background_jobs_started':[]})
    __import__('atexit').register(cleanup_temp)
    # Remove provider/network and deployment secret inputs rather than persisting them.
    for key in list(env):
        if key.startswith(('OPENAI_','DEEPSEEK_','QCLAW_','AI_','DJANGO_')):env.pop(key)
    before_inventory=inventory()
    commands=[]
    def run(label,cmd,cwd=ROOT,expected=(0,)):
        start=dt.datetime.now().astimezone().isoformat();t=time.monotonic()
        r=subprocess.run([str(x) for x in cmd],cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (out/(label+'.stdout.txt')).write_text(r.stdout,encoding='utf-8');(out/(label+'.stderr.txt')).write_text(r.stderr,encoding='utf-8')
        record={'id':label,'command':subprocess.list2cmdline([str(x) for x in cmd]),'cwd':str(cwd),'started_at':start,'exit_code':r.returncode,'expected_exit_codes':list(expected),'passed':r.returncode in expected,'seconds':round(time.monotonic()-t,3)}
        commands.append(record);dump(out/'commands.json',commands);print(f"{label}: exit {r.returncode}",flush=True)
        if r.returncode not in expected:
            dump(out/'failed.json',record);print(r.stdout[-4000:]);print(r.stderr[-4000:]);raise RuntimeError(f'{label} failed; evidence retained in {out}')
        return r
    py=Path(a.python).resolve();npm=shutil.which('npm.cmd') or shutil.which('npm')
    if not npm:raise RuntimeError('npm missing')
    run('toolchain',[py,'-c','import sys,django,rest_framework,sqlite3,json; print(json.dumps({"python":sys.version,"django":django.get_version(),"drf":rest_framework.VERSION,"sqlite":sqlite3.sqlite_version}))'])
    run('python-freeze',[py,'-m','pip','freeze','--all'])
    run('node-version',['node','--version']);run('npm-version',[npm,'--version'])
    top=run('git-boundary',['git','-C',str(ROOT),'rev-parse','--show-toplevel']).stdout.strip()
    if Path(top).resolve()!=ROOT:raise RuntimeError('Not isolated Git root')
    run('git-remotes',['git','-C',str(ROOT),'remote','-v'])
    # Compare copied 146-file historical source, immutable original clean tree and ZIP.
    baseline=json.loads((ROOT/'docs/harness/baseline/source-files.json').read_text(encoding='utf-8-sig'))
    legacy=ROOT.parent/'ram-admin-review-20261117'
    protection={'legacy_source_available':(legacy/'clean-source').is_dir(),'original_clean_files_verified':0,'zip_verified':False,'vendor_files_verified':0}
    if protection['legacy_source_available']:
        for row in baseline:
            assert sha((legacy/'clean-source'/row['path']).read_bytes())==row['sha256'],row['path']
        protection['original_clean_files_verified']=len(baseline)
        archive=legacy/'ram-admin-clean-source-3a4fd98-local-patched.zip'
        assert sha(archive.read_bytes())=='69f462c7eb086f0e62e49def92299f76a90c42fa4eea1384bfccaf42cf936141'
        protection['zip_verified']=True
    vendor=ROOT/'docs/harness/vendor/1.0.0'
    for line in (vendor/'SHA256SUMS.txt').read_text(encoding='utf-8-sig').splitlines():
        digest,rel=line.split('  ',1);assert sha((vendor/rel).read_bytes())==digest,rel
        protection['vendor_files_verified']+=1
    version=(ROOT/'VERSION').read_text().strip();pkg=json.loads((ROOT/'frontend/package.json').read_text());lock=json.loads((ROOT/'frontend/package-lock.json').read_text())
    assert version==pkg['version']==lock['version']==lock['packages']['']['version']=='0.3.0-dev.1'
    inherited=json.loads((ROOT/'docs/harness/baseline/harness.1-protection.json').read_text(encoding='utf-8-sig'))
    oldroot=Path(inherited['source'])
    assert oldroot.is_dir(),'Protected .1 source unavailable'
    for row in inherited['files']:assert sha((oldroot/row['path']).read_bytes())==row['sha256'],row['path']
    protection['harness_1_original_files_verified']=len(inherited['files'])
    assert sha((ROOT/'backend/apps/ai/tests.py').read_bytes())==sha((oldroot/'backend/apps/ai/tests.py').read_bytes()),'Token baseline tests changed'
    protection['token_25_tests_unchanged']=True
    protection['consistent_version']=version
    previous=json.loads((ROOT/'docs/harness/baseline/harness.2-protection.json').read_text())
    previous_root=Path(previous['source'])
    for item in previous['files']:assert sha((previous_root/item['path']).read_bytes())==item['sha256'],item['path']
    protection['harness_2_original_files_verified']=len(previous['files'])
    for rel in ['backend/apps/ai/tests.py','backend/apps/rbac/test_core.py','backend/apps/rbac/test_concurrency.py','backend/apps/rbac/tests.py','tools/verify_migrations.py']:
        if (previous_root/rel).exists():assert sha((ROOT/rel).read_bytes())==sha((previous_root/rel).read_bytes()),rel
    import ast
    oldtree=ast.parse((previous_root/'tools/verify_boss.py').read_text(encoding='utf-8'));newtree=ast.parse((ROOT/'tools/verify_boss.py').read_text(encoding='utf-8'))
    getchecks=lambda tree:[ast.dump(n,include_attributes=False) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='check'][:26]
    assert getchecks(oldtree)==getchecks(newtree)
    assert sha((ROOT/'tools/verify_boss.py').read_bytes())==sha((previous_root/'tools/verify_boss.py').read_bytes()),'Original BOSS28 file changed'
    protection['original_boss_first_26_unchanged']=True
    dump(out/'source-protection.json',protection)
    run('django-check',[py,'backend/manage.py','check','--settings=config.settings.test'])
    run('migration-drift',[py,'backend/manage.py','makemigrations','--check','--dry-run','--settings=config.settings.test'])
    focused=run('token-focused',[py,'backend/manage.py','test','apps.ai','--settings=config.settings.test','-v','2'])
    full=run('django-all',[py,'manage.py','test','--settings=config.settings.test','-v','2'],ROOT/'backend')
    run('migration-lifecycle',[py,'tools/verify_migrations.py','--output',str(out/'migration.json')])
    run('boss-regression',[py,'tools/verify_boss.py','--output',str(out/'boss.json')])
    run('core-boundaries',[py,'tools/verify_core_boundaries.py','--output',str(out/'core-boundaries.json')])
    run('sqlite-ops',[py,'tools/verify_ops.py','--output',str(out/'ops.json')])
    if not a.skip_install:run('npm-ci',[npm,'ci','--ignore-scripts'],ROOT/'frontend')
    else:commands.append({'id':'npm-ci','status':'not-run','reason':'explicit --skip-install uses existing installed node_modules; clean install not asserted'})
    run('frontend-typecheck',[npm,'run','typecheck'],ROOT/'frontend')
    run('frontend-build',[npm,'run','build'],ROOT/'frontend')
    live=None
    if a.browser_python:
        lived=run('browser-e2e',[py,'tools/verify_live.py','--python',py,'--browser-python',a.browser_python])
        live_ref=json.loads(lived.stdout.strip().splitlines()[-1])
        live=json.loads((Path(live_ref['run'])/'live-summary.json').read_text(encoding='utf-8'))
        assert live['status']=='pass' and live['backend_stopped'] and live['isolated_data_removed']
        dump(out/'live-binding.json',{'run':live_ref['run'],'http_checks':len(live['checks'])-1,'browser_checks':live['browser']['check_count'],'summary_sha256':sha((Path(live_ref['run'])/'live-summary.json').read_bytes())})
    cli=ROOT/'docs/harness/vendor/1.0.0/tools/harness.py'
    run('harness-lint',[py,cli,'lint','--root',ROOT,'--manifest','harness.json'])
    run('harness-routing',[py,'tools/harness_checks.py','--output',str(out/'routing.json')])
    rows=inventory()
    assert rows==before_inventory,'Source changed during verification; rerun on frozen source'
    digest=sha(json.dumps(rows,sort_keys=True,separators=(',',':')).encode())
    dump(out/'source-inventory.json',{'dirty_digest':digest,'files':rows})
    baseline_map={r['path']:r['sha256'] for r in baseline};current={r['path']:r['sha256'] for r in rows}
    changes={'modified':[x for x in baseline_map if x in current and baseline_map[x]!=current[x]],'removed':[x for x in baseline_map if x not in current],'added':[x for x in current if x not in baseline_map]}
    dump(out/'changes.json',changes)
    assert not changes['removed'],'Historical source file removed'
    forbidden=[x['path'] for x in rows if re.search(r'(^|/)(\.env($|\.)|local-demo-account)|\.(sqlite3?|db|pem|key)$',x['path'],re.I)]
    assert not forbidden,forbidden
    build=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'size':p.stat().st_size} for p in sorted((ROOT/'frontend/dist').rglob('*')) if p.is_file()]
    dump(out/'frontend-artifacts.json',build)
    def count(text):
        m=re.search(r'Ran (\d+) tests?',text);assert m,text[-1000:];return int(m[1])
    counts={'token_tests':count(focused.stderr+focused.stdout),'django_discovery_tests':count(full.stderr+full.stdout),'boss_assertions':json.loads((out/'boss.json').read_text())['check_count'],'migration_assertions':json.loads((out/'migration.json').read_text())['check_count'],'routing_probes':json.loads((out/'routing.json').read_text())['check_count']}
    counts['core_and_production_boundary_checks']=json.loads((out/'core-boundaries.json').read_text())['check_count']
    counts['sqlite_ops_checks']=json.loads((out/'ops.json').read_text())['check_count']
    if live:counts.update(real_http_checks=len(live['checks'])-1,real_browser_checks=live['browser']['check_count'])
    # All pass records bind exact source/env/artifacts and concrete local component target.
    h=lambda x:sha(json.dumps(x,sort_keys=True).encode())
    versions=json.loads((out/'toolchain.stdout.txt').read_text())
    environment={'os':platform.platform(),'arch':platform.machine(),'shell':'Python subprocess launched from PowerShell','toolchain_digest':h(versions),'config_digest':h({'settings':'config.settings.test','providers':[],'webhook':'','ephemeral_test_secrets':True}),'permissions_digest':h({'scope':'new isolated source only','remote_release_authorized':False}),'dependencies_digest':sha((out/'python-freeze.stdout.txt').read_bytes()+(ROOT/'frontend/package-lock.json').read_bytes())}
    artifact_names=['source-inventory.json','migration.json','boss.json','routing.json','frontend-artifacts.json','core-boundaries.json','ops.json']
    if live:artifact_names.append('live-binding.json')
    artifacts=[{'path':(out/n).relative_to(ROOT).as_posix(),'sha256':sha((out/n).read_bytes())} for n in artifact_names]
    task={'schema_version':1,'change_id':'CORE-003-0.3.0-dev.1','tasks':['fix','security','api','data','ui','build','docs'],'paths':changes['modified']+[p for p in changes['added'] if not p.startswith('docs/harness/vendor/')],'platforms':['web-api','sqlite','web-frontend'],'domains':['security','api','data','build','docs'],'effects':['schema','local-files','local-tests'],'actions':['edit','test'],'lifecycle':'verification','facts':{'has_frontend':True,'has_database':True},'approved_paths':['**'],'source':{'base_commit':'3a4fd98bb98030c67261a4973048c6ba133a828e+9-local-patches','commit':'uncommitted-isolated-prerelease','dirty_digest':digest},'environment':environment,'target':{'kind':'local-component-tests-and-build','id':'ram-admin-0.3.0-dev.1-Windows-SQLite-isolated','version':f"Django {versions['django']} DRF {versions['drf']} SQLite {versions['sqlite']}",'simulated':False},'artifacts':artifacts}
    dump(out/'task.json',task)
    resolved=run('harness-resolve',[py,cli,'resolve','--root',ROOT,'--manifest','harness.json','--task',(out/'task.json').relative_to(ROOT).as_posix()])
    # commands.json was bound before resolve. Preserve that artifact snapshot separately.
    # Rebind task artifacts after command recording to avoid digest mismatch.
    task['artifacts']=[{'path':x['path'],'sha256':sha((ROOT/x['path']).read_bytes())} for x in task['artifacts']]
    dump(out/'task.json',task)
    resolved=subprocess.run([str(py),str(cli),'resolve','--root',str(ROOT),'--manifest','harness.json','--task',(out/'task.json').relative_to(ROOT).as_posix()],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
    assert resolved.returncode==0,resolved.stdout
    resolution=json.loads(resolved.stdout);dump(out/'resolution.json',resolution)
    manifest=json.loads((ROOT/'harness.json').read_text());now=dt.datetime.now(dt.timezone.utc);records=[]
    command_map={c['id']:c for c in commands if 'command'in c}
    mapping={'product-tests':'django-all','migration-tests':'migration-lifecycle','frontend-build':'frontend-build','harness-routing':'harness-routing','browser-e2e':'browser-e2e'}
    for rule in manifest['rules']:
        if not set(rule['scope']['tasks'])&set(task['tasks']):continue
        for check in rule['evidence_refs']:
            label=mapping.get(check);c=command_map.get(label)
            records.append({'id':rule['id']+'-'+check,'change_id':task['change_id'],'rule_id':rule['id'],'rule_revision':rule['revision'],'check_id':check,'executor_id':'verify','executor_version':'1','status':'pass' if c else 'not-run','scope':rule['scope'],'routing_digest':resolution['routing_digest'],'source':task['source'],'environment':environment,'target':task['target'],'artifacts':task['artifacts'],'collected_at':now.isoformat(),'valid_until':(now+dt.timedelta(days=7)).isoformat(),'invalidation_triggers':['source','environment','target','artifacts','rule','executor','scope','change','routing'],'execution':{'performed':bool(c),'command':c['command'] if c else 'Browser/HTTP E2E not executed','cwd':(Path(c['cwd']).relative_to(ROOT).as_posix() if Path(c['cwd']) != ROOT else '.') if c else '.','exit_code':c['exit_code'] if c else None,'observation':f'Local assertions only; counts={counts}' if c else 'New-version live server/browser journey not run; component tests are not E2E.'},'na_basis':None,'limitations':['No production acceptance, human security signoff, remote CI enforcement or browser E2E claim.']})
    dump(out/'records.json',{'schema_version':1,'records':records})
    e=subprocess.run([str(py),str(cli),'evidence','--root',str(ROOT),'--manifest','harness.json','--task',(out/'task.json').relative_to(ROOT).as_posix(),'--records',(out/'records.json').relative_to(ROOT).as_posix(),'--now',dt.datetime.now(dt.timezone.utc).isoformat()],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
    (out/'evidence-evaluation.json').write_text(e.stdout,encoding='utf-8');(out/'evidence-evaluation.stderr.txt').write_text(e.stderr,encoding='utf-8')
    assert e.returncode==(0 if live else 2),(e.returncode,e.stdout,e.stderr)
    evaluation=json.loads(e.stdout)
    assert evaluation['status']==('pass' if live else 'not-run'),evaluation
    summary={'version':version,'local_checks_status':'pass','overall_product_status':'not-run','harness_evidence_status':evaluation['status'],'harness_evidence_exit_code':e.returncode,'run':out.relative_to(ROOT).as_posix(),'source_dirty_digest':digest,'counts':counts,'protection':protection,'not_run':['Human visual acceptance and physical devices' if live else 'New-version real HTTP server/browser E2E and human visual acceptance','Real external AI provider','Production deployment/rollback/recovery and interrupted migration failure injection (local isolated SQLite restore separately tested)','Concurrent revoke stress test and cancellation of already-authorized in-flight requests','Remote CI required checks/branch protection/signatures/license audit','eslint: inherited script references missing eslint dependency'],'background_jobs_started':[],'human_signoff':'pending independent acceptance; no fabricated signature'}
    summary['core_local_status']='pass' if live else 'not-run'
    summary['live_run']=str(Path(live_ref['run']).relative_to(ROOT)) if live else None
    dump(out/'summary.json',summary);dump(EVIDENCE/'latest.json',{'run':summary['run'],'summary':(out/'summary.json').relative_to(ROOT).as_posix()})
    dump(ROOT/'release-manifest.json',{'version':version,'release_status':'local-prerelease-unpublished','upstream_head':'3a4fd98bb98030c67261a4973048c6ba133a828e','source_archive_sha256':'69f462c7eb086f0e62e49def92299f76a90c42fa4eea1384bfccaf42cf936141','source_inventory':(out/'source-inventory.json').relative_to(ROOT).as_posix(),'source_dirty_digest':digest,'verification_summary':(out/'summary.json').relative_to(ROOT).as_posix(),'contains_local_accounts_or_database':False,'remote_release_authorized':False})
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
