"""Run published commands and shipped JSON schema validation; offline only."""
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('harness',ROOT/'tools/harness.py')
h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
commands=[
(['--version'],0,None),
(['tools/harness.py','--help'],0,None),
(['tools/harness.py','lint','--root','examples/demo','--manifest','harness.json'],0,'pass'),
(['tools/harness.py','resolve','--root','examples/demo','--manifest','harness.json','--task','tasks/hybrid.json'],0,'pass'),
(['tools/harness.py','evidence','--root','examples/demo','--manifest','harness.json','--task','tasks/hybrid.json','--records','evidence/records.json','--now','2026-11-14T10:00:00Z'],2,'not-run'),
(['tools/harness.py','lint','--root','.','--manifest','profiles/platforms/harness.json'],0,'pass'),
]
for name,code,status in [('static-web-release',0,'pass'),('hybrid',0,'pass'),('unknown-web-db',2,'blocked')]:
    commands.append((['tools/harness.py','resolve','--root','.','--manifest','profiles/platforms/harness.json','--task','profiles/platforms/tasks/'+name+'.json'],code,status))
commands.append((['tools/harness.py','evidence','--root','.','--manifest','profiles/platforms/harness.json','--task','profiles/platforms/tasks/hybrid.json','--records','profiles/platforms/evidence/records.json','--now','2026-11-14T10:00:00Z'],2,'not-run'))
commands.append((['profiles/check_platforms.py'],0,None))
results=[]
for args,expected,status in commands:
    cp=subprocess.run([sys.executable]+args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    data=None
    try: data=json.loads(cp.stdout)
    except ValueError: pass
    ok=cp.returncode==expected and (status is None or isinstance(data,dict) and data.get('status')==status)
    results.append({'command':'python '+' '.join(args),'expected_exit':expected,'exit':cp.returncode,'expected_status':status,'status':data.get('status') if isinstance(data,dict) else None,'pass':ok,'output':data if data is not None else (cp.stdout+cp.stderr)[-2500:]})
instances=[]
for base in ('examples','profiles'):
    for path in sorted((ROOT/base).rglob('*.json')):
        try:
            obj=h.read_json(path)
            kind='manifest' if path.name=='harness.json' else 'evidence' if path.name=='records.json' else 'task'
            h.validate(obj,h.read_json(ROOT/'schemas'/(kind+'.schema.json')))
            instances.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),'schema':kind,'pass':True})
        except Exception as exc:
            instances.append({'path':str(path.relative_to(ROOT)),'pass':False,'error':str(exc)})
report={'python':sys.version,'platform':platform.platform(),'executable':sys.executable,'commands':results,'instances':instances,'failed':sum(not x['pass'] for x in results+instances),'scope':'published CLI command behavior and shipped JSON shape; not product execution or remote CI'}
(ROOT/'qa/integration-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'commands':len(results),'json_instances':len(instances),'failed':report['failed'],'failures':[r for r in results+instances if not r['pass']]},ensure_ascii=False,indent=2))
sys.exit(bool(report['failed']))
