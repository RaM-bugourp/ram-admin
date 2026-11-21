"""Maintainer-only deterministic asset generator; not used by the read-only CLI."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def obj(props, required=None):
    return {'type': 'object', 'properties': props, 'required': list(props) if required is None else required, 'additionalProperties': False}
def arr(item, minimum=0):
    return {'type': 'array', 'items': item, 'minItems': minimum, 'uniqueItems': True}
def enum(*values): return {'type': 'string', 'enum': list(values)}
def save(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
def text(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8')

S = {'type': 'string', 'minLength': 1}
STRINGS = arr(S)
NONEMPTY = arr(S, 1)
SHA = {'type': 'string', 'pattern': '^[a-f0-9]{64}$'}
REV = {'type': 'integer', 'minimum': 1}
VERSION = {'type': 'integer', 'const': 1}
SCOPE = obj({k: NONEMPTY for k in ('actions', 'paths', 'platforms', 'tasks', 'lifecycle')} | {'exclusions': STRINGS})
SOURCE = obj({'base_commit': S, 'commit': S, 'dirty_digest': SHA})
ENV = obj({k: S if k in ('os', 'arch', 'shell') else SHA for k in ('os', 'arch', 'shell', 'toolchain_digest', 'config_digest', 'permissions_digest', 'dependencies_digest')})
TARGET = obj({'kind': S, 'id': S, 'version': S, 'simulated': {'type': 'boolean'}})
ARTIFACT = obj({'path': S, 'sha256': SHA})
ARTIFACTS = arr(ARTIFACT)
ENFORCEMENT = enum('proposed', 'advisory', 'enforced')
RULE = obj({'id': S, 'revision': REV, 'owner': S, 'scope': SCOPE, 'source': S, 'statement': S, 'enforcement': ENFORCEMENT, 'executor_refs': NONEMPTY, 'evidence_refs': NONEMPTY, 'constraints': arr(obj({'key': S, 'value': S}))})
MATCH = obj({k: STRINGS for k in ('tasks', 'paths', 'platforms', 'domains', 'effects')} | {'mode': enum('all', 'task-or-path')})
CONDITION = obj({'when': obj({'fact': S, 'equals': {'type': 'boolean'}}), 'add': NONEMPTY})
ROUTE = obj({'id': S, 'owner': S, 'match': MATCH, 'context_set': obj({'required': NONEMPTY, 'conditional': arr(CONDITION)}), 'rule_refs': NONEMPTY, 'executor_refs': NONEMPTY, 'evidence_refs': NONEMPTY})
MANIFEST = obj({'schema_version': VERSION, 'project_id': S, 'owners': arr(obj({'id': S, 'contact': S, 'backup': S}), 1), 'executors': arr(obj({'id': S, 'version': S, 'kind': enum('manual', 'automated', 'schema')}), 1), 'rules': arr(RULE, 1), 'routes': arr(ROUTE, 1)})
TASK = obj({'schema_version': VERSION, 'change_id': S, **{k: NONEMPTY for k in ('tasks', 'paths', 'platforms', 'actions', 'approved_paths')}, **{k: STRINGS for k in ('domains', 'effects')}, 'lifecycle': S, 'facts': {'type': 'object', 'additionalProperties': {'type': ['boolean', 'null']}}, 'source': SOURCE, 'environment': ENV, 'target': TARGET, 'artifacts': ARTIFACTS})
NA = obj({'reason': S, 'scope_dimension': enum('tasks', 'paths', 'platforms', 'actions', 'lifecycle'), 'excluded_values': NONEMPTY})
NA['type'] = ['object', 'null']
RECORD = obj({'id': S, 'change_id': S, 'rule_id': S, 'rule_revision': REV, 'check_id': S, 'executor_id': S, 'executor_version': S, 'status': enum('pass', 'fail', 'blocked', 'not-run', 'not-applicable'), 'scope': SCOPE, 'routing_digest': SHA, 'source': SOURCE, 'environment': ENV, 'target': TARGET, 'artifacts': ARTIFACTS, 'collected_at': S, 'valid_until': S, 'invalidation_triggers': arr(enum('change', 'source', 'environment', 'target', 'artifacts', 'rule', 'executor', 'scope', 'routing'), 9), 'execution': obj({'performed': {'type': 'boolean'}, 'command': {'type': 'string'}, 'cwd': S, 'exit_code': {'type': ['integer', 'null']}, 'observation': {'type': 'string'}}), 'na_basis': NA, 'limitations': STRINGS})
EVIDENCE = obj({'schema_version': VERSION, 'records': arr(RECORD)})
for name, schema in [('manifest', MANIFEST), ('task', TASK), ('evidence', EVIDENCE), ('route', ROUTE), ('rule', RULE)]:
    save('schemas/' + name + '.schema.json', {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': 'urn:harness:v1:' + name, 'title': 'Harness v1 ' + name, **schema})

base = 'examples/demo/'
for page in ('core', 'plugin', 'web', 'app', 'data'):
    text(base + 'pages/' + page + '.md', '# ' + page.title() + ' demonstration context\n\nSynthetic example only. This page is not a product acceptance record.\n')
text(base + 'artifacts/fixture.txt', 'SYNTHETIC FIXTURE: not real product validation\n')
sha = hashlib.sha256((ROOT / base / 'artifacts/fixture.txt').read_bytes()).hexdigest()
manifest = {'schema_version': 1, 'project_id': 'synthetic-cross-domain-demo', 'owners': [{'id': 'maintainers', 'contact': 'example-owner@example.invalid', 'backup': 'example-backup@example.invalid'}], 'executors': [{'id': 'observe-target', 'version': '1.0.0', 'kind': 'manual'}], 'rules': [], 'routes': []}
for platform in ('plugin', 'web', 'app'):
    rule = {'id': platform.upper() + '-VERIFY', 'revision': 1, 'owner': 'maintainers', 'scope': {'actions': ['edit', 'release'], 'paths': ['src/' + platform + '/**'], 'platforms': [platform], 'tasks': ['feature', 'release'], 'lifecycle': ['development', 'release'], 'exclusions': []}, 'source': 'pages/' + platform + '.md', 'statement': 'Collect representative real target evidence before claiming product pass.', 'enforcement': 'proposed', 'executor_refs': ['observe-target'], 'evidence_refs': [platform + '-target-check'], 'constraints': [{'key': 'preserve-tests', 'value': 'required'}]}
    route = {'id': 'route.' + platform, 'owner': 'maintainers', 'match': {'tasks': ['feature', 'release'], 'paths': ['src/' + platform + '/**'], 'platforms': [platform], 'domains': [], 'effects': [], 'mode': 'all'}, 'context_set': {'required': ['pages/core.md', 'pages/' + platform + '.md'], 'conditional': [{'when': {'fact': 'changes_persistence', 'equals': True}, 'add': ['pages/data.md']}]}, 'rule_refs': [rule['id']], 'executor_refs': ['observe-target'], 'evidence_refs': [platform + '-target-check']}
    manifest['rules'].append(rule); manifest['routes'].append(route)
save(base + 'harness.json', manifest)
common = {'schema_version': 1, 'change_id': 'demo-change-001', 'tasks': ['feature'], 'paths': [], 'platforms': [], 'domains': ['ui'], 'effects': [], 'actions': ['edit'], 'lifecycle': 'development', 'facts': {'changes_persistence': True}, 'approved_paths': ['src/**'], 'source': {'base_commit': 'synthetic-base-001', 'commit': 'synthetic-source-002', 'dirty_digest': '0' * 64}, 'environment': {'os': 'fixture-os', 'arch': 'fixture-arch', 'shell': 'fixture-shell', **{k: '1' * 64 for k in ('toolchain_digest', 'config_digest', 'permissions_digest', 'dependencies_digest')}}, 'target': {'kind': 'fixture', 'id': 'synthetic-demo-instance-001', 'version': '1', 'simulated': True}, 'artifacts': [{'path': 'artifacts/fixture.txt', 'sha256': sha}]}
for platform in ('plugin', 'web', 'app', 'hybrid'):
    task = copy.deepcopy(common)
    task['platforms'] = ['plugin', 'web', 'app'] if platform == 'hybrid' else [platform]
    task['paths'] = ['src/' + p + '/feature.txt' for p in task['platforms']]
    save(base + 'tasks/' + platform + '.json', task)
import importlib.util
module_spec = importlib.util.spec_from_file_location('harness_generator_core', ROOT / 'tools/harness.py')
core = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(core)
hybrid = json.loads((ROOT / base / 'tasks/hybrid.json').read_text(encoding='utf-8'))
fingerprint = core.routing_fingerprint(ROOT / base, manifest, hybrid)
records = []
for rule in manifest['rules']:
    record = {k: copy.deepcopy(common[k]) for k in ('change_id', 'source', 'environment', 'target', 'artifacts')}
    record.update({'id': 'record.' + rule['id'], 'rule_id': rule['id'], 'rule_revision': 1, 'routing_digest': fingerprint, 'check_id': rule['evidence_refs'][0], 'executor_id': 'observe-target', 'executor_version': '1.0.0', 'status': 'not-run', 'scope': rule['scope'], 'collected_at': '2026-11-14T09:00:00Z', 'valid_until': '2026-11-15T09:00:00Z', 'invalidation_triggers': ['change', 'source', 'environment', 'target', 'artifacts', 'rule', 'executor', 'scope', 'routing'], 'execution': {'performed': False, 'command': '', 'cwd': '.', 'exit_code': None, 'observation': 'Synthetic example: real host/service/device unavailable; no product validation executed.'}, 'na_basis': None, 'limitations': ['SYNTHETIC FIXTURE ONLY; not real product evidence']})
    records.append(record)
save(base + 'evidence/records.json', {'schema_version': 1, 'records': records})
print('Generated 5 schemas, shared demo pages/artifact, 4 task profiles, not-run evidence bundle.')
