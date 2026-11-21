"""Project advisory routing tests; not product or authorization gates."""
import argparse, copy, hashlib, json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'docs/harness/vendor/1.0.0/tools/harness.py'

def sha(data):return hashlib.sha256(data).hexdigest()
def task_template():
    h=sha(b'routing-test-explicit-state')
    return {'schema_version':1,'change_id':'routing-discovery-probe','tasks':['docs'],'paths':['docs/harness/PLAN.md'],'platforms':['web-api'],'domains':['security'],'effects':['local-files'],'actions':['edit'],'lifecycle':'development','facts':{'has_frontend':True,'has_database':True},'approved_paths':['**'],'source':{'base_commit':'3a4fd98bb98030c67261a4973048c6ba133a828e+local-patched-source','commit':'uncommitted-prerelease','dirty_digest':h},'environment':{'os':'Windows','arch':'x64','shell':'PowerShell','toolchain_digest':h,'config_digest':h,'permissions_digest':h,'dependencies_digest':h},'target':{'kind':'routing-probe','id':'ram-admin-isolated-prerelease-discovery','version':'0.2.0-harness.1','simulated':True},'artifacts':[]}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    records=[]
    with tempfile.TemporaryDirectory(prefix='ram-route-',dir=ROOT/'docs/harness/evidence') as tmp:
        directory=Path(tmp)
        def run(label, task, expected, codes=(), manifest='harness.json'):
            path=directory/(label+'.json');path.write_text(json.dumps(task),encoding='utf-8')
            cmd=[sys.executable,str(CLI),'resolve','--root',str(ROOT),'--manifest',manifest,'--task',path.relative_to(ROOT).as_posix()]
            r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8')
            result=json.loads(r.stdout);actual={e['code'] for e in result.get('errors',[])}
            assert r.returncode==expected,(label,r.returncode,result)
            assert set(codes)<=actual,(label,actual)
            if expected==0:
                assert {'AGENTS.md','docs/harness/PLAN.md','docs/harness/OWNERS.md'} <= set(result['context_files']),label
                assert 'docs/harness/vendor/1.0.0/docs/platforms/web/frontend.md' in result['context_files'],label
            if label=='cross-domain-union':
                assert {'RAM-API-001','RAM-DATA-001','RAM-DOC-001','RAM-BUILD-001'} <= set(result['applicable_rules'])
            records.append({'name':label,'exit_code':r.returncode,'status':result['status'],'error_codes':sorted(actual),'routing_digest':result.get('routing_digest'),'contexts':result.get('context_files',[])})
            return result
        for family in ['fix','feature','api','security','data','ui','build','docs']:
            t=task_template();t['tasks']=[family];run('family-'+family,t,0)
        t=task_template();t['tasks']=['security','api','data','build','docs'];run('cross-domain-union',t,0)
        t=task_template();t['facts']['has_frontend']=None;run('unknown-fact',t,2)
        t=task_template();t['approved_paths']=['frontend/**'];run('unauthorized-path',t,2)
        t=task_template();t['tasks']=['unregistered'];run('no-route',t,2)
        # Scope conflict only in a temporary project-owned manifest, not production rules.
        manifest=json.loads((ROOT/'harness.json').read_text(encoding='utf-8'))
        doc=next(r for r in manifest['rules'] if r['id']=='RAM-DOC-001')
        doc['constraints']=[{'key':'probe-conflict','value':'keep'}]
        other=copy.deepcopy(doc);other['id']='RAM-CONFLICT-PROBE';other['constraints']=[{'key':'probe-conflict','value':'remove'}];manifest['rules'].append(other)
        route=next(r for r in manifest['routes'] if r['id']=='route-doc');route['rule_refs'].append(other['id'])
        mp=directory/'conflict-manifest.json';mp.write_text(json.dumps(manifest),encoding='utf-8')
        run('explicit-conflict',task_template(),2,manifest=mp.relative_to(ROOT).as_posix())
        # Missing evidence demonstrates that successful resolve cannot fake target execution.
        t=task_template();tp=directory/'missing-evidence-task.json';tp.write_text(json.dumps(t),encoding='utf-8')
        ep=directory/'empty-records.json';ep.write_text(json.dumps({'schema_version':1,'records':[]}),encoding='utf-8')
        r=subprocess.run([sys.executable,str(CLI),'evidence','--root',str(ROOT),'--manifest','harness.json','--task',tp.relative_to(ROOT).as_posix(),'--records',ep.relative_to(ROOT).as_posix(),'--now',__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()],capture_output=True,text=True,encoding='utf-8')
        assert r.returncode==2,r.stdout
        records.append({'name':'missing-product-evidence-not-pass','exit_code':2,'status':json.loads(r.stdout)['status']})
    output={'status':'pass','checks':records,'check_count':len(records),'limitations':['Offline route discovery and schema assertions only; not product PASS or hard enforcement.','Template simulated routing targets are never used as product pass evidence.','Human owner review still required for natural language conflicts and authorization.']}
    Path(a.output).write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(output,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
