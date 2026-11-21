#!/usr/bin/env python3
"""Offline, read-only Harness v1 checker. Never executes manifest commands."""
import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent.parent / 'schemas'
TRIGGERS = {'change', 'source', 'environment', 'target', 'artifacts', 'rule', 'executor', 'scope', 'routing'}

class Invalid(Exception):
    def __init__(self, code, path, message):
        self.error = {'code': code, 'path': path, 'message': message}
        super().__init__(message)

def fail(code, path, message):
    raise Invalid(code, path, message)

def unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        check_unicode(key)
        if key in obj:
            fail('E_DUPLICATE_KEY', '$', 'duplicate JSON key: ' + key)
        obj[key] = value
    return obj

def check_unicode(value):
    if isinstance(value, str):
        if any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            fail('E_UNICODE', '$', 'JSON strings must contain Unicode scalar values; isolated surrogate rejected')
    elif isinstance(value, dict):
        for key, item in value.items():
            check_unicode(key)
            check_unicode(item)
    elif isinstance(value, list):
        for item in value:
            check_unicode(item)

def read_json(path):
    try:
        obj = json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_pairs, parse_constant=lambda x: fail('E_JSON', '$', 'nonfinite number ' + x))
        check_unicode(obj)
        return obj
    except (ValueError, UnicodeError) as exc:
        fail('E_JSON', str(path), str(exc))

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

def safe(root, value, pointer, must_exist=True, pattern=False):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value or value.startswith('/') or value.endswith('/') or any(x in ('', '.', '..') for x in value.split('/')):
        fail('E_PATH', pointer, 'expected normalized root-relative POSIX path')
    if not pattern and any(c in value for c in '*?'):
        fail('E_PATH', pointer, 'wildcard not allowed in file reference')
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        fail('E_PATH_ESCAPE', pointer, 'reference escapes project root')
    if must_exist and not path.is_file():
        fail('E_MISSING_FILE', pointer, value)
    return path

def timestamp(value, pointer):
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', value):
            raise ValueError('timezone-qualified RFC3339 required')
        result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.utcoffset() is None:
            raise ValueError('timezone required')
        return result
    except (ValueError, TypeError) as exc:
        fail('E_TIME', pointer, str(exc))

def check_schema(schema, pointer='$schema'):
    """Inspect the complete schema, including branches absent from the instance."""
    supported = {'$schema', '$id', 'title', 'description', 'type', 'properties', 'required', 'additionalProperties', 'items', 'minItems', 'uniqueItems', 'minLength', 'pattern', 'enum', 'const', 'minimum'}
    if not isinstance(schema, dict):
        fail('E_SCHEMA', pointer, 'schema must be an object')
    if set(schema) - supported:
        fail('E_SCHEMA_KEYWORD', pointer, str(sorted(set(schema) - supported)))
    types = schema.get('type', [])
    types = [types] if isinstance(types, str) else types
    if not isinstance(types, list) or ('type' in schema and not types) or any(not isinstance(t, str) or t not in ('object', 'array', 'string', 'integer', 'boolean', 'null') for t in types) or len(set(types)) != len(types):
        fail('E_SCHEMA', pointer + '/type', 'unsupported or duplicate type')
    if not isinstance(schema.get('properties', {}), dict):
        fail('E_SCHEMA', pointer + '/properties', 'expected object')
    required = schema.get('required', [])
    if not isinstance(required, list) or any(not isinstance(x, str) for x in required) or len(set(required)) != len(required):
        fail('E_SCHEMA', pointer + '/required', 'expected unique string array')
    for key in ('minItems', 'minLength'):
        if key in schema and (type(schema[key]) is not int or schema[key] < 0):
            fail('E_SCHEMA', pointer + '/' + key, 'expected nonnegative integer')
    if 'uniqueItems' in schema and type(schema['uniqueItems']) is not bool:
        fail('E_SCHEMA', pointer + '/uniqueItems', 'expected boolean')
    if 'minimum' in schema and type(schema['minimum']) not in (int, float):
        fail('E_SCHEMA', pointer + '/minimum', 'expected number')
    if 'enum' in schema and (not isinstance(schema['enum'], list) or not schema['enum']):
        fail('E_SCHEMA', pointer + '/enum', 'expected nonempty array')
    for key in ('$schema', '$id', 'title', 'description', 'pattern'):
        if key in schema and not isinstance(schema[key], str):
            fail('E_SCHEMA', pointer + '/' + key, 'expected string')
    if 'pattern' in schema:
        try:
            re.compile(schema['pattern'])
        except re.error as exc:
            fail('E_SCHEMA', pointer + '/pattern', str(exc))
    for key, child in schema.get('properties', {}).items():
        check_schema(child, pointer + '/properties/' + key)
    if 'items' in schema:
        check_schema(schema['items'], pointer + '/items')
    additional = schema.get('additionalProperties', True)
    if isinstance(additional, dict):
        check_schema(additional, pointer + '/additionalProperties')
    elif type(additional) is not bool:
        fail('E_SCHEMA', pointer + '/additionalProperties', 'expected boolean or schema')

def validate(value, schema, pointer='$', _checked=False):
    # Bounded Draft 2020-12 subset; check all schema branches before instance walk.
    if not _checked:
        check_schema(schema)
    types = schema.get('type', [])
    types = [types] if isinstance(types, str) else types
    matches = {'object': isinstance(value, dict), 'array': isinstance(value, list), 'string': isinstance(value, str), 'integer': type(value) is int or (type(value) is float and value.is_integer()), 'boolean': type(value) is bool, 'null': value is None}
    if types and not any(matches.get(t, False) for t in types):
        fail('E_TYPE', pointer, 'expected ' + '|'.join(types))
    if 'const' in schema and (type(value) is not type(schema['const']) or value != schema['const']):
        fail('E_CONST', pointer, 'unexpected constant')
    if 'enum' in schema and not any(type(value) is type(x) and value == x for x in schema['enum']):
        fail('E_ENUM', pointer, 'unexpected value')
    if isinstance(value, dict):
        props = schema.get('properties', {})
        for key in schema.get('required', []):
            if key not in value:
                fail('E_REQUIRED', pointer + '/' + key, 'missing field')
        for key, item in value.items():
            child = props.get(key, schema.get('additionalProperties', True))
            if child is False:
                fail('E_UNKNOWN_FIELD', pointer + '/' + key, 'unknown field')
            if isinstance(child, dict):
                validate(item, child, pointer + '/' + key)
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            fail('E_MIN_ITEMS', pointer, 'too few items')
        if schema.get('uniqueItems') and len({json.dumps(x, sort_keys=True) for x in value}) != len(value):
            fail('E_DUPLICATE', pointer, 'duplicate array item')
        for i, item in enumerate(value):
            if 'items' in schema:
                validate(item, schema['items'], pointer + '/' + str(i))
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0):
            fail('E_EMPTY', pointer, 'string too short')
        if 'pattern' in schema and re.search(schema['pattern'], value) is None:
            fail('E_PATTERN', pointer, 'invalid string format')
    if type(value) in (int, float) and value < schema.get('minimum', value):
        fail('E_MINIMUM', pointer, 'integer below minimum')

def load(root, relative, kind):
    obj = read_json(safe(root, relative, '$input'))
    validate(obj, read_json(SCHEMA_DIR / (kind + '.schema.json')))
    return obj

def glob_match(path, pattern):
    # ** is special only when it occupies a complete segment.
    parts = pattern.split('/')
    rx = ''
    for i, part in enumerate(parts):
        if part == '**':
            rx += '(?:[^/]+/)*' if i < len(parts) - 1 else '(?:[^/]+(?:/[^/]+)*)?'
        else:
            rx += ''.join('[^/]*' if c == '*' else '[^/]' if c == '?' else re.escape(c) for c in part)
            if i < len(parts) - 1:
                rx += '/'
    return re.fullmatch(rx, path) is not None

def intersects(values, choices):
    return not choices or '*' in choices or bool(set(values) & set(choices))

def paths_match(paths, patterns):
    return not patterns or any(glob_match(p, q) for p in paths for q in patterns)

def scope_applies(scope, task):
    return (all(intersects(task[key] if key != 'lifecycle' else [task[key]], scope[key]) for key in ('actions', 'tasks', 'platforms', 'lifecycle')) and any(paths_match([p], scope['paths']) and not any(glob_match(p, q) for q in scope['exclusions']) for p in task['paths']))

def route_matches(route, task):
    match = route['match']
    task_match = intersects(task['tasks'], match['tasks'])
    path_match = paths_match(task['paths'], match['paths'])
    if match['mode'] == 'task-or-path':
        selected = (bool(match['tasks']) and task_match) or (bool(match['paths']) and path_match)
    else:
        selected = task_match and path_match
    return selected and all(intersects(task[key], match[key]) for key in ('platforms', 'domains', 'effects'))

def indexes(manifest):
    result = {}
    for key in ('owners', 'executors', 'rules', 'routes'):
        result[key] = {}
        for i, item in enumerate(manifest[key]):
            if item['id'] in result[key]:
                fail('E_DUPLICATE_ID', '$/' + key + '/' + str(i) + '/id', item['id'])
            result[key][item['id']] = item
    return result

def lint(root, manifest):
    ix = indexes(manifest)
    used = set()
    def ref(kind, value, pointer):
        if value not in ix[kind]:
            fail('E_REF', pointer, 'unknown ' + kind + ': ' + value)
    for i, rule in enumerate(manifest['rules']):
        p = '$/rules/' + str(i)
        ref('owners', rule['owner'], p + '/owner')
        safe(root, rule['source'], p + '/source')
        for pattern in rule['scope']['paths'] + rule['scope']['exclusions']:
            safe(root, pattern, p + '/scope', must_exist=False, pattern=True)
        for value in rule['executor_refs']:
            ref('executors', value, p + '/executor_refs')
        keys = [x['key'] for x in rule['constraints']]
        if len(set(keys)) != len(keys):
            fail('E_DUPLICATE', p + '/constraints', 'duplicate constraint key')
    for i, route in enumerate(manifest['routes']):
        p = '$/routes/' + str(i)
        ref('owners', route['owner'], p + '/owner')
        for pattern in route['match']['paths']:
            safe(root, pattern, p + '/match/paths', must_exist=False, pattern=True)
        for page in route['context_set']['required'] + [x for c in route['context_set']['conditional'] for x in c['add']]:
            safe(root, page, p + '/context_set')
        for value in route['executor_refs']:
            ref('executors', value, p + '/executor_refs')
        for value in route['rule_refs']:
            ref('rules', value, p + '/rule_refs')
            used.add(value)
            rule = ix['rules'][value]
            if not set(rule['executor_refs']).issubset(route['executor_refs']) or not set(rule['evidence_refs']).issubset(route['evidence_refs']):
                fail('E_REF_CLOSURE', p, 'route must include rule executor/check references')
        checks = {x for r in route['rule_refs'] for x in ix['rules'][r]['evidence_refs']}
        executors = {x for r in route['rule_refs'] for x in ix['rules'][r]['executor_refs']}
        if set(route['executor_refs']) - executors:
            fail('E_ORPHAN_EXECUTOR', p + '/executor_refs', 'executor not owned by referenced rule')
        if set(route['evidence_refs']) - checks:
            fail('E_ORPHAN_CHECK', p + '/evidence_refs', 'check not owned by referenced rule')
    if set(ix['rules']) - used:
        fail('E_ORPHAN_RULE', '$/rules', ','.join(sorted(set(ix['rules']) - used)))
    return ix

def artifacts_check(root, artifacts, pointer):
    seen = set()
    for i, artifact in enumerate(artifacts):
        if artifact['path'] in seen:
            fail('E_DUPLICATE', pointer + '/' + str(i) + '/path', 'duplicate artifact path')
        seen.add(artifact['path'])
        path = safe(root, artifact['path'], pointer + '/' + str(i) + '/path')
        if hashlib.sha256(path.read_bytes()).hexdigest() != artifact['sha256']:
            fail('E_ARTIFACT_DIGEST', pointer + '/' + str(i) + '/sha256', 'artifact bytes differ')

def task_check(root, task):
    for key in ('paths', 'approved_paths'):
        for value in task[key]:
            safe(root, value, '$/' + key, must_exist=False, pattern=key == 'approved_paths')
    if task['target']['id'].strip().lower() in {'local', 'latest', 'unknown', 'localhost'}:
        fail('E_TARGET', '$/target/id', 'concrete target instance required')
    artifacts_check(root, task['artifacts'], '$/artifacts')

def routing_fingerprint(root, manifest, task):
    pages = {r['source'] for r in manifest['rules']}
    for route in manifest['routes']:
        pages.update(route['context_set']['required'])
        pages.update(p for c in route['context_set']['conditional'] for p in c['add'])
    page_digests = {p: hashlib.sha256(safe(root, p, '$context').read_bytes()).hexdigest() for p in sorted(pages)}
    return digest({'manifest': manifest, 'task': task, 'context_digests': page_digests})

def route_covers_path(route, task, path):
    match = route['match']
    return paths_match([path], match['paths']) or (match['mode'] == 'task-or-path' and bool(match['tasks']) and intersects(task['tasks'], match['tasks']))

def route_covers_value(route, task, dimension, value):
    if dimension == 'paths':
        return route_covers_path(route, task, value)
    match = route['match']
    return intersects([value], match[dimension]) or (dimension == 'tasks' and match['mode'] == 'task-or-path' and bool(match['paths']) and paths_match(task['paths'], match['paths']))

def resolve(root, manifest, task):
    ix = lint(root, manifest)
    task_check(root, task)
    matched = [x for x in manifest['routes'] if route_matches(x, task)]
    issues, pages, rule_ids, executors, checks = [], set(), set(), set(), set()
    if not matched:
        issues.append({'code': 'E_UNROUTED', 'path': '$/routes', 'message': 'no route matched; read-only discovery required'})
    for route in matched:
        pages.update(route['context_set']['required'])
        rule_ids.update(route['rule_refs'])
        executors.update(route['executor_refs'])
        checks.update(route['evidence_refs'])
        for condition in route['context_set']['conditional']:
            fact = condition['when']['fact']
            value = task['facts'].get(fact)
            if value is None:
                issues.append({'code': 'E_CONDITION_UNKNOWN', 'path': '$/facts/' + fact, 'message': 'cannot determine conditional context for ' + route['id']})
            elif value == condition['when']['equals']:
                pages.update(condition['add'])
    for dimension in ('tasks', 'paths', 'platforms', 'domains', 'effects'):
        uncovered = [value for value in task[dimension] if not any(route_covers_value(route, task, dimension, value) for route in matched)]
        if uncovered:
            issues.append({'code': 'E_UNCOVERED_DIMENSION', 'path': '$/' + dimension, 'message': 'reroute uncovered values: ' + ','.join(uncovered)})
    applicable = [ix['rules'][r] for r in sorted(rule_ids) if scope_applies(ix['rules'][r]['scope'], task)]
    conflicts = []
    for i, a in enumerate(applicable):
        for b in applicable[i + 1:]:
            ca = {c['key']: c['value'] for c in a['constraints']}
            cb = {c['key']: c['value'] for c in b['constraints']}
            common_actions = [action for action in task['actions'] if intersects([action], a['scope']['actions']) and intersects([action], b['scope']['actions'])]
            common_paths = [p for p in task['paths'] if paths_match([p], a['scope']['paths']) and paths_match([p], b['scope']['paths']) and not any(glob_match(p, q) for q in a['scope']['exclusions'] + b['scope']['exclusions'])]
            for key in sorted(ca.keys() & cb.keys()):
                if ca[key] != cb[key] and common_actions and common_paths and all(any(intersects([value], a['scope'][dimension]) and intersects([value], b['scope'][dimension]) for value in task[dimension]) for dimension in ('tasks', 'platforms')):
                    conflicts.append({'rules': [a['id'], b['id']], 'revisions': [a['revision'], b['revision']], 'owners': [a['owner'], b['owner']], 'key': key, 'actions': common_actions, 'paths': common_paths})
    outside = [p for p in task['paths'] if not any(glob_match(p, q) for q in task['approved_paths'])]
    if outside:
        issues.append({'code': 'E_OUT_OF_SCOPE', 'path': '$/paths', 'message': 'outside approved_paths: ' + ','.join(outside)})
    if conflicts:
        issues.append({'code': 'E_SCOPE_CONFLICT', 'path': '$/rules', 'message': 'stop affected actions and escalate to listed owners'})
    return {'schema_version': 1, 'status': 'blocked' if issues else 'pass', 'errors': issues, 'matched_routes': sorted(x['id'] for x in matched), 'unmatched_routes': sorted(x['id'] for x in manifest['routes'] if x not in matched), 'context_files': sorted(pages), 'rule_refs': sorted(rule_ids), 'applicable_rules': [r['id'] for r in applicable], 'executor_refs': sorted(executors), 'evidence_refs': sorted(checks), 'conflicts': conflicts, 'stopped_actions': sorted(set(task['actions'] if any(e['code'] != 'E_SCOPE_CONFLICT' for e in issues) else []) | {a for c in conflicts for a in c['actions']}), 'routing_digest': routing_fingerprint(root, manifest, task), 'reroute_on': ['task dimensions or facts change', 'diff expands or source changes', 'environment target artifacts or rules change'], 'limitations': ['declared task state is not external authorization', 'only explicit constraint-key conflicts detected']}

def aggregate(states):
    for state in ('fail', 'blocked', 'not-run'):
        if state in states:
            return state
    return 'pass' if 'pass' in states else 'not-applicable'

def na_check(record, rule, task, pointer):
    basis = record['na_basis']
    if not basis or scope_applies(rule['scope'], task):
        fail('E_NA_SCOPE', pointer + '/na_basis', 'N/A requires a genuinely excluded rule scope')
    key = basis['scope_dimension']
    values = task[key] if key != 'lifecycle' else [task[key]]
    scope = rule['scope']
    if set(basis['excluded_values']) != set(values):
        fail('E_NA_SCOPE', pointer + '/na_basis', 'basis must identify current dimension values')
    excluded = not intersects(values, scope[key]) if key != 'paths' else not any(paths_match([p], scope['paths']) and not any(glob_match(p, q) for q in scope['exclusions']) for p in values)
    if not excluded:
        fail('E_NA_SCOPE', pointer + '/na_basis', 'declared dimension does not exclude task')

def evidence(root, manifest, task, bundle, now):
    routing = resolve(root, manifest, task)
    ix = indexes(manifest)
    current, seen, ids = [], set(), set()
    for i, record in enumerate(bundle['records']):
        p = '$/records/' + str(i)
        pair = (record['rule_id'], record['check_id'])
        if record['id'] in ids or pair in seen:
            fail('E_DUPLICATE_ID', p, 'duplicate record or rule/check pair')
        ids.add(record['id']); seen.add(pair)
        if record['rule_id'] not in ix['rules'] or record['executor_id'] not in ix['executors']:
            fail('E_REF', p, 'unknown rule or executor')
        rule = ix['rules'][record['rule_id']]
        executor = ix['executors'][record['executor_id']]
        if record['check_id'] not in rule['evidence_refs'] or record['executor_id'] not in rule['executor_refs']:
            fail('E_REF', p, 'check/executor is not associated with rule')
        if not TRIGGERS.issubset(record['invalidation_triggers']):
            fail('E_VALIDITY', p + '/invalidation_triggers', 'missing mandatory invalidation trigger')
        start = timestamp(record['collected_at'], p + '/collected_at')
        end = timestamp(record['valid_until'], p + '/valid_until')
        if end <= start:
            fail('E_VALIDITY', p + '/valid_until', 'validity must be finite and later than collection')
        safe(root, record['execution']['cwd'], p + '/execution/cwd', must_exist=False) if record['execution']['cwd'] != '.' else None
        artifacts_check(root, record['artifacts'], p + '/artifacts')
        if record['status'] == 'pass':
            run = record['execution']
            if not run['performed'] or run['exit_code'] != 0 or not run['command'].strip() or not run['observation'].strip() or not record['artifacts'] or executor['kind'] == 'schema' or record['target']['simulated']:
                fail('E_FAKE_PASS', p, 'pass requires observed nonsimulated execution, successful exit and artifacts; schema checks are not product evidence')
        if record['status'] == 'not-applicable':
            na_check(record, rule, task, p)
        elif record['na_basis'] is not None:
            fail('E_NA_SCOPE', p + '/na_basis', 'basis only allowed with not-applicable')
        reasons = []
        for key in ('change_id', 'source', 'environment', 'target', 'artifacts'):
            if record[key] != task[key]:
                reasons.append(key + '-changed')
        if record['rule_revision'] != rule['revision']: reasons.append('rule-revision-changed')
        if record['executor_version'] != executor['version']: reasons.append('executor-version-changed')
        if record['scope'] != rule['scope']: reasons.append('scope-changed')
        if record['routing_digest'] != routing['routing_digest']: reasons.append('routing-changed')
        if now < start: reasons.append('not-yet-valid')
        if now >= end: reasons.append('expired')
        relevant = record['rule_id'] in routing['applicable_rules']
        current.append({'id': record['id'], 'rule_id': record['rule_id'], 'check_id': record['check_id'], 'historical_status': record['status'], 'current_status': 'not-run' if reasons else record['status'], 'invalidation_reasons': reasons, 'enforcement': rule['enforcement'], 'required': relevant, 'scope_basis': None if relevant else {'reason': 'rule outside currently applicable routed scope', 'declared_na_basis': record['na_basis']}})
    for rid in routing['applicable_rules']:
        for check in ix['rules'][rid]['evidence_refs']:
            if (rid, check) not in seen:
                current.append({'id': None, 'rule_id': rid, 'check_id': check, 'historical_status': None, 'current_status': 'not-run', 'invalidation_reasons': ['missing-record'], 'enforcement': ix['rules'][rid]['enforcement'], 'required': True})
    states = [x['current_status'] for x in current if x['required']]
    if routing['errors']: states.append('blocked')
    status = aggregate(states)
    return {'schema_version': 1, 'status': status, 'errors': routing['errors'], 'records': current, 'routing_digest': routing['routing_digest'], 'scope_basis': {'applicable_rules': routing['applicable_rules'], 'matched_routes': routing['matched_routes']}, 'limitations': ['unverified declarations: offline consistency only; performed/target/authorization are not authenticated', 'does not execute tests, authorize actions or verify external enforcement']}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    for name in ('lint', 'resolve', 'evidence'):
        sub = subs.add_parser(name, help={'lint': 'validate manifest shape and references only', 'resolve': 'union task context and detect blocked actions', 'evidence': 'check current evidence bindings without running commands'}[name])
        sub.add_argument('--root', required=True, help='project root; references cannot escape')
        sub.add_argument('--manifest', default='harness.json', help='root-relative manifest path')
        if name != 'lint': sub.add_argument('--task', required=True, help='root-relative task JSON')
        if name == 'evidence':
            sub.add_argument('--records', required=True, help='root-relative evidence bundle JSON')
            sub.add_argument('--now', help='timezone-qualified RFC3339; defaults to current UTC')
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).resolve(strict=True)
        manifest = load(root, args.manifest, 'manifest')
        if args.command == 'lint':
            lint(root, manifest)
            result = {'schema_version': 1, 'status': 'pass', 'errors': [], 'counts': {k: len(manifest[k]) for k in ('owners', 'executors', 'rules', 'routes')}, 'limitations': ['structure/reference validation only, not execution evidence or authorization']}
        else:
            task = load(root, args.task, 'task')
            if args.command == 'resolve': result = resolve(root, manifest, task)
            else:
                bundle = load(root, args.records, 'evidence')
                now = timestamp(args.now, '$now') if args.now else dt.datetime.now(dt.timezone.utc)
                result = evidence(root, manifest, task, bundle, now)
        code = 0 if result['status'] in ('pass', 'not-applicable') else 2
    except Invalid as exc:
        result, code = {'schema_version': 1, 'status': 'invalid', 'errors': [exc.error]}, 1
    except OSError as exc:
        result, code = {'schema_version': 1, 'status': 'error', 'errors': [{'code': 'E_IO', 'path': '$', 'message': str(exc)}]}, 3
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code

if __name__ == '__main__':
    sys.exit(main())
