"""Independent synthetic acceptance. Run: python qa/acceptance.py. No product claims."""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('harness', ROOT / 'tools/harness.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
NOW = h.timestamp('2026-11-14T10:00:00Z', '$now')
results = []

def case(name, fn):
    try:
        detail = fn()
        results.append({'name': name, 'pass': True, 'detail': detail})
    except Exception as exc:
        results.append({'name': name, 'pass': False, 'detail': str(exc)})

def require(ok, detail='assertion failed'):
    if not ok:
        raise AssertionError(detail)

def reject(fn, code=None):
    try:
        fn()
    except h.Invalid as exc:
        require(code is None or exc.error['code'] == code, exc.error)
        return exc.error
    raise AssertionError('unexpected acceptance')

with tempfile.TemporaryDirectory(prefix='harness-qa-') as tmp:
    root = Path(tmp).resolve()
    (root / 'pages').mkdir()
    for name in ('base', 'extra', 'second'):
        (root / 'pages' / (name + '.md')).write_text('# ' + name, encoding='utf-8')
    (root / 'artifact.txt').write_text('synthetic evidence; never product proof', encoding='utf-8')
    art = [{'path': 'artifact.txt', 'sha256': hashlib.sha256((root / 'artifact.txt').read_bytes()).hexdigest()}]
    scope = {'actions': ['edit'], 'paths': ['src/**'], 'platforms': ['web'], 'tasks': ['feature'], 'lifecycle': ['development'], 'exclusions': []}
    rule = {'id': 'RULE', 'revision': 1, 'owner': 'owner', 'scope': scope, 'source': 'pages/base.md', 'statement': 'Synthetic assertion', 'enforcement': 'proposed', 'executor_refs': ['observer'], 'evidence_refs': ['check'], 'constraints': [{'key': 'safety', 'value': 'keep'}]}
    route = {'id': 'route', 'owner': 'owner', 'match': {'tasks': ['feature'], 'paths': ['src/**'], 'platforms': ['web'], 'domains': [], 'effects': [], 'mode': 'all'}, 'context_set': {'required': ['pages/base.md'], 'conditional': [{'when': {'fact': 'db', 'equals': True}, 'add': ['pages/extra.md']}]}, 'rule_refs': ['RULE'], 'executor_refs': ['observer'], 'evidence_refs': ['check']}
    manifest = {'schema_version': 1, 'project_id': 'independent-synthetic', 'owners': [{'id': 'owner', 'contact': 'owner@example.invalid', 'backup': 'backup@example.invalid'}], 'executors': [{'id': 'observer', 'version': '1', 'kind': 'manual'}], 'rules': [rule], 'routes': [route]}
    task = {'schema_version': 1, 'change_id': 'qa-change', 'tasks': ['feature'], 'paths': ['src/a.txt'], 'platforms': ['web'], 'domains': [], 'effects': [], 'actions': ['edit'], 'lifecycle': 'development', 'facts': {'db': False}, 'approved_paths': ['src/**'], 'source': {'base_commit': 'qa-base', 'commit': 'qa-head', 'dirty_digest': 'a'*64}, 'environment': {'os': 'qa-os', 'arch': 'qa-arch', 'shell': 'qa-shell', 'toolchain_digest': 'b'*64, 'config_digest': 'c'*64, 'permissions_digest': 'd'*64, 'dependencies_digest': 'e'*64}, 'target': {'kind': 'service', 'id': 'qa-isolated-instance-001', 'version': '1', 'simulated': False}, 'artifacts': art}
    record = {'id': 'record', 'change_id': task['change_id'], 'rule_id': 'RULE', 'rule_revision': 1, 'check_id': 'check', 'executor_id': 'observer', 'executor_version': '1', 'status': 'pass', 'scope': copy.deepcopy(scope), 'source': copy.deepcopy(task['source']), 'environment': copy.deepcopy(task['environment']), 'target': copy.deepcopy(task['target']), 'artifacts': copy.deepcopy(art), 'collected_at': '2026-11-14T09:00:00Z', 'valid_until': '2026-11-14T11:00:00Z', 'invalidation_triggers': sorted(h.TRIGGERS), 'execution': {'performed': True, 'command': 'synthetic observation description; not executed', 'cwd': '.', 'exit_code': 0, 'observation': 'self-reported fixture only'}, 'na_basis': None, 'limitations': ['synthetic, not authentic product evidence']}
    record['routing_digest'] = h.routing_fingerprint(root, manifest, task)
    def clone(x): return copy.deepcopy(x)
    def resolve(m=None, t=None): return h.resolve(root, m or manifest, t or task)
    def evidence(r=None, m=None, t=None, now=NOW): return h.evidence(root, m or manifest, t or task, {'schema_version': 1, 'records': [record if r is None else r]}, now)
    def shape(obj, kind): return h.validate(obj, h.read_json(ROOT / 'schemas' / (kind + '.schema.json')))
    case('independent fixture schema manifest', lambda: shape(manifest, 'manifest'))
    case('independent fixture schema task', lambda: shape(task, 'task'))
    case('independent fixture schema evidence', lambda: shape({'schema_version': 1, 'records': [record]}, 'evidence'))
    case('valid routing', lambda: require(resolve()['status'] == 'pass'))
    case('consistent self-reported pass remains proposed', lambda: require(evidence()['status'] == 'pass' and evidence()['records'][0]['enforcement'] == 'proposed' and 'offline' in evidence()['limitations'][0]))
    def union():
        m = clone(manifest); second = clone(route); second['id'] = 'second'; second['context_set']['required'] = ['pages/second.md', 'pages/base.md']; m['routes'].append(second)
        out = resolve(m); require(out['matched_routes'] == ['route', 'second'] and out['context_files'] == ['pages/base.md', 'pages/second.md'])
        require(out == resolve(m), 'nondeterministic repeat'); return out['context_files']
    case('route union dedup and deterministic repeat', union)
    for value in (True, False, None, 'absent'):
        def condition(value=value):
            t=clone(task); t['facts'] = {} if value == 'absent' else {'db': value}; out=resolve(t=t)
            require(out['status'] == ('blocked' if value is None or value == 'absent' else 'pass'))
            require(('pages/extra.md' in out['context_files']) == (value is True)); return out['status']
        case('conditional ' + str(value), condition)
    def unmatched():
        t=clone(task); t['tasks']=['unknown']; out=resolve(t=t); require(out['status']=='blocked' and any(e['code']=='E_UNROUTED' for e in out['errors']))
    case('unknown unmatched task blocked', unmatched)
    for branch in ('path-only','task-only'):
        def or_positive(branch=branch):
            m=clone(manifest); t=clone(task); m['routes'][0]['match']['mode']='task-or-path'
            if branch=='path-only': m['routes'][0]['match']['tasks']=['refactor']
            else: m['routes'][0]['match']['paths']=['other/**']
            out=resolve(m,t); require(out['status']=='pass' and out['matched_routes']==['route'],out); return out['status']
        case('OR route positive '+branch,or_positive)
    for dimension,excluded in [('platforms',['app']),('domains',['security']),('effects',['deploy'])]:
        def or_and(dimension=dimension,excluded=excluded):
            m=clone(manifest); m['routes'][0]['match']['mode']='task-or-path'; m['routes'][0]['match']['tasks']=['refactor']; m['routes'][0]['match'][dimension]=excluded
            out=resolve(m); require(out['status']=='blocked' and out['matched_routes']==[],out); return out['status']
        case('OR does not bypass AND '+dimension,or_and)
    def literal_brackets():
        m=clone(manifest); t=clone(task); (root/'pages/[policy].md').write_text('# Literal brackets',encoding='utf-8')
        m['rules'][0]['source']='pages/[policy].md'; m['routes'][0]['context_set']['required']=['pages/[policy].md']; t['paths']=['src/[id].tsx']; t['approved_paths']=['src/[id].tsx']
        out=resolve(m,t); require(out['status']=='pass',out); require(h.glob_match('src/[id].tsx','src/[id].tsx')); require(not h.glob_match('src/i.tsx','src/[id].tsx')); return out['context_files']
    case('literal brackets valid references and paths',literal_brackets)
    def boundary():
        t=clone(task); t['paths']=['src/ab']; t['approved_paths']=['src/a']; require(resolve(t=t)['status']=='blocked')
    case('approved path prefix is not authority', boundary)
    for path, pattern, expected in [('a.txt','**/a.txt',True),('a/b/a.txt','**/a.txt',True),('src/a.txt','src/**',True),('src/a/b.txt','src/**',True),('src/ab','src/a',False),('src/a','src/?',True)]:
        case('glob '+path+' '+pattern, lambda p=path,g=pattern,e=expected: require(h.glob_match(p,g)==e))
    def multidim():
        t=clone(task); t['platforms']=['app']; require(not h.scope_applies(scope,t)); t['platforms']=['app','web']; require(h.scope_applies(scope,t))
    case('scope dimensions AND entries OR', multidim)
    def conflict():
        m=clone(manifest); r=clone(rule); r['id']='OTHER'; r['constraints'][0]['value']='remove'; m['rules'].append(r); m['routes'][0]['rule_refs'].append('OTHER'); out=resolve(m); require(out['status']=='blocked' and out['conflicts'] and out['stopped_actions']==['edit'])
    case('hard constraint conflict stops edit', conflict)
    for kind in ('owners','executors','rules','routes'):
        def dup(kind=kind):
            m=clone(manifest); m[kind].append(clone(m[kind][0])); return reject(lambda:h.lint(root,m),'E_DUPLICATE_ID')
        case('duplicate ID '+kind,dup)
    for field,value in [('source','../outside.md'),('source','C:/secret.txt'),('source','/etc/passwd'),('source','\\\\host\\secret'),('source','pages\\base.md'),('source','pages/missing.md')]:
        def badpath(field=field,value=value):
            m=clone(manifest); m['rules'][0][field]=value; return reject(lambda:h.lint(root,m))
        case('unsafe/missing path '+value,badpath)
    def orphan():
        m=clone(manifest); m['routes'][0]['evidence_refs'].append('unowned'); return reject(lambda:h.lint(root,m),'E_ORPHAN_CHECK')
    case('route-only evidence cannot vanish',orphan)
    def missingref():
        m=clone(manifest); m['rules'][0]['owner']='missing'; return reject(lambda:h.lint(root,m),'E_REF')
    case('dangling owner reference',missingref)
    def unknownfield():
        m=clone(manifest); m['typo']=True; return reject(lambda:shape(m,'manifest'),'E_UNKNOWN_FIELD')
    case('unknown manifest field rejected',unknownfield)
    case('unknown schema keyword rejected',lambda:reject(lambda:h.validate({}, {'type':'object','anyOf':[]}), 'E_SCHEMA_KEYWORD'))
    case('nested absent schema keyword rejected',lambda:reject(lambda:h.validate({}, {'type':'object','properties':{'absent':{'type':'string','unknownKeyword':True}}}), 'E_SCHEMA_KEYWORD'))
    case('nested empty-array schema keyword rejected',lambda:reject(lambda:h.validate([], {'type':'array','items':{'type':'string','unknownKeyword':True}}), 'E_SCHEMA_KEYWORD'))
    case('duplicate JSON key rejected',lambda:reject(lambda:h.unique_pairs([('x',1),('x',2)]),'E_DUPLICATE_KEY'))
    for key,subkey,value in [('target','id','foreign-target'),('source','dirty_digest','f'*64),('environment','config_digest','f'*64)]:
        def stale(key=key,subkey=subkey,value=value):
            r=clone(record); r[key][subkey]=value; out=evidence(r); require(out['status']=='not-run' and out['records'][0]['historical_status']=='pass'); return out['records'][0]['invalidation_reasons']
        case('stale binding '+key+'.'+subkey,stale)
    for field,value in [('paths',['src/a.txt','src/b.txt']),('facts',{'db':True}),('approved_paths',['src/a.txt'])]:
        def reroute(field=field,value=value):
            t=clone(task); t[field]=value; out=evidence(t=t); require(out['status']=='not-run' and 'routing-changed' in out['records'][0]['invalidation_reasons']); return out['records'][0]['invalidation_reasons']
        case('routing digest changes '+field,reroute)
    def prose():
        path=root/'pages/base.md'; before=path.read_text(encoding='utf-8')
        try:
            path.write_text(before+' changed',encoding='utf-8'); out=evidence(); require(out['status']=='not-run' and 'routing-changed' in out['records'][0]['invalidation_reasons'])
        finally: path.write_text(before,encoding='utf-8')
    case('routing digest changes source page bytes',prose)
    case('expiry invalidates at exclusive end',lambda:require(evidence(now=h.timestamp(record['valid_until'],'$'))['status']=='not-run'))
    for key,value in [('rule_revision',2),('executor_version','2')]:
        def version(key=key,value=value):
            r=clone(record); r[key]=value; require(evidence(r)['status']=='not-run')
        case('changed '+key,version)
    def artifact():
        r=clone(record); r['artifacts'][0]['sha256']='0'*64; return reject(lambda:evidence(r),'E_ARTIFACT_DIGEST')
    case('altered artifact rejected',artifact)
    for state in ('pass','fail','blocked','not-run'):
        def states(state=state):
            r=clone(record); r['status']=state; require(evidence(r)['status']==state)
        case('canonical state '+state,states)
    for states,expected in [(['pass','fail'],'fail'),(['not-run','blocked'],'blocked'),(['pass','not-run'],'not-run'),(['not-applicable'],'not-applicable'),([], 'not-applicable')]:
        case('aggregate '+str(states),lambda s=states,e=expected:require(h.aggregate(s)==e))
    def badna():
        r=clone(record); r['status']='not-applicable'; r['na_basis']={'reason':'no device','scope_dimension':'platforms','excluded_values':['web']}; return reject(lambda:evidence(r),'E_NA_SCOPE')
    case('applicable N/A rejected',badna)
    def validna():
        m=clone(manifest); m['rules'][0]['scope']['platforms']=['app']; r=clone(record); r['scope']=clone(m['rules'][0]['scope']); r['routing_digest']=h.routing_fingerprint(root,m,task); r['status']='not-applicable'; r['na_basis']={'reason':'web task excludes app scope','scope_dimension':'platforms','excluded_values':['web']}; out=evidence(r,m); require(out['status']=='not-applicable' and out['scope_basis']['applicable_rules']==[]); return out['scope_basis']
    case('justified excluded N/A reachable',validna)
    for field,value in [('performed',False),('exit_code',1),('command',''),('observation','')]:
        def fake(field=field,value=value):
            r=clone(record); r['execution'][field]=value; return reject(lambda:evidence(r),'E_FAKE_PASS')
        case('invalid pass '+field,fake)
    def simulated():
        r=clone(record); r['target']['simulated']=True; return reject(lambda:evidence(r),'E_FAKE_PASS')
    case('simulated target cannot product pass',simulated)
    def shell():
        sentinel=root/'MUST_NOT_EXIST'; r=clone(record); r['execution']['command']='echo PWNED > "'+str(sentinel)+'"'; out=evidence(r); require(out['status']=='pass' and not sentinel.exists()); return 'command accepted only as data; no shell execution'
    case('shell payload remains inert data',shell)
    def cli():
        for name,obj in [('harness.json',manifest),('task.json',task),('records.json',{'schema_version':1,'records':[record]})]:
            (root/name).write_text(json.dumps(obj),encoding='utf-8')
        outputs=[]
        for command in ('lint','resolve','evidence'):
            args=[sys.executable,str(ROOT/'tools/harness.py'),command,'--root',str(root),'--manifest','harness.json']
            if command!='lint': args+=['--task','task.json']
            if command=='evidence': args+=['--records','records.json','--now','2026-11-14T10:00:00Z']
            cp=subprocess.run(args,capture_output=True,text=True); require(cp.returncode==0,cp.stderr+cp.stdout); outputs.append({'command':command,'exit':cp.returncode,'status':json.loads(cp.stdout)['status']})
        return outputs
    case('real CLI smoke three operations',cli)
    for value,expected in [(chr(0xd800),1),('中文🙂',0)]:
        def unicode_cli(value=value,expected=expected):
            t=clone(task); t['change_id']=value
            (root/'unicode-task.json').write_text(json.dumps(t),encoding='utf-8')
            cp=subprocess.run([sys.executable,str(ROOT/'tools/harness.py'),'resolve','--root',str(root),'--manifest','harness.json','--task','unicode-task.json'],capture_output=True,encoding='utf-8')
            require(cp.returncode==expected,repr(cp.stdout)+repr(cp.stderr)); out=json.loads(cp.stdout)
            require('Traceback' not in cp.stderr,cp.stderr)
            require(out['status']==('pass' if expected==0 else 'invalid'),out)
            return {'exit':cp.returncode,'status':out['status']}
        case('CLI valid Chinese emoji' if expected==0 else 'CLI lone surrogate structured rejection',unicode_cli)

report={'synthetic_only':True,'python':sys.version,'cases':len(results),'passed':sum(x['pass'] for x in results),'failed':sum(not x['pass'] for x in results),'results':results}
(ROOT/'qa/results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(bool(report['failed']))
