import copy
import datetime as dt
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('harness', ROOT / 'tools/harness.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
NOW = dt.datetime(2026, 11, 14, 10, tzinfo=dt.timezone.utc)

class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'project'
        shutil.copytree(ROOT / 'examples/demo', self.root)
        self.m = h.load(self.root, 'harness.json', 'manifest')
        self.t = h.load(self.root, 'tasks/hybrid.json', 'task')
        self.b = h.load(self.root, 'evidence/records.json', 'evidence')

    def error(self, code, fn):
        with self.assertRaises(h.Invalid) as result:
            fn()
        self.assertEqual(result.exception.error['code'], code)
        self.assertTrue(result.exception.error['path'])

    def checked(self):
        return h.evidence(self.root, self.m, self.t, self.b, NOW)

    def passing(self):
        # Synthetic unit-test declarations, never a product verification.
        self.t['target']['simulated'] = False
        fingerprint = h.routing_fingerprint(self.root, self.m, self.t)
        for record in self.b['records']:
            record['routing_digest'] = fingerprint
            record['target']['simulated'] = False
            record['status'] = 'pass'
            record['execution'].update(performed=True, command='unit-fixture-observation', exit_code=0, observation='Synthetic positive envelope contract fixture')

    def cli(self, command, *extra):
        out = io.StringIO()
        with redirect_stdout(out):
            code = h.main([command, '--root', str(self.root), *extra])
        return code, json.loads(out.getvalue())

    def test_lint_demo(self):
        self.assertEqual(len(h.lint(self.root, self.m)['routes']), 3)

    def test_union_cross_platform(self):
        result = h.resolve(self.root, self.m, self.t)
        self.assertEqual(result['matched_routes'], ['route.app', 'route.plugin', 'route.web'])
        self.assertEqual(len(result['context_files']), 5)
        self.assertEqual(len(result['applicable_rules']), 3)

    def test_individual_platform_profiles(self):
        for platform in ('plugin', 'web', 'app'):
            with self.subTest(platform=platform):
                task = h.load(self.root, 'tasks/' + platform + '.json', 'task')
                result = h.resolve(self.root, self.m, task)
                self.assertEqual(result['matched_routes'], ['route.' + platform])
                self.assertEqual(result['status'], 'pass')

    def test_conditional_false_does_not_add(self):
        self.t['facts']['changes_persistence'] = False
        self.assertNotIn('pages/data.md', h.resolve(self.root, self.m, self.t)['context_files'])

    def test_missing_condition_blocks(self):
        self.t['facts'] = {}
        result = h.resolve(self.root, self.m, self.t)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('E_CONDITION_UNKNOWN', [e['code'] for e in result['errors']])

    def test_null_condition_blocks(self):
        self.t['facts']['changes_persistence'] = None
        self.assertEqual(h.resolve(self.root, self.m, self.t)['status'], 'blocked')

    def test_unknown_manifest_field(self):
        self.m['execute'] = 'should-never-run'
        self.error('E_UNKNOWN_FIELD', lambda: h.validate(self.m, h.read_json(h.SCHEMA_DIR / 'manifest.schema.json')))

    def test_unknown_nested_field(self):
        self.t['source']['extra'] = 1
        self.error('E_UNKNOWN_FIELD', lambda: h.validate(self.t, h.read_json(h.SCHEMA_DIR / 'task.schema.json')))

    def test_missing_required_field(self):
        del self.t['target']
        self.error('E_REQUIRED', lambda: h.validate(self.t, h.read_json(h.SCHEMA_DIR / 'task.schema.json')))

    def test_duplicate_ids(self):
        self.m['owners'].append(copy.deepcopy(self.m['owners'][0]))
        self.error('E_DUPLICATE_ID', lambda: h.lint(self.root, self.m))

    def test_duplicate_json_key(self):
        path = self.root / 'duplicate.json'
        path.write_text('{"schema_version":1,"schema_version":1}', encoding='utf-8')
        self.error('E_DUPLICATE_KEY', lambda: h.read_json(path))

    def test_nonfinite_json_rejected(self):
        path = self.root / 'nonfinite.json'
        path.write_text('{"x":NaN}', encoding='utf-8')
        self.error('E_JSON', lambda: h.read_json(path))

    def test_boolean_is_not_revision(self):
        self.m['rules'][0]['revision'] = True
        self.error('E_TYPE', lambda: h.validate(self.m, h.read_json(h.SCHEMA_DIR / 'manifest.schema.json')))

    def test_missing_context_page(self):
        (self.root / 'pages/data.md').unlink()
        self.error('E_MISSING_FILE', lambda: h.lint(self.root, self.m))

    def test_missing_source_page(self):
        self.m['rules'][0]['source'] = 'pages/missing.md'
        self.error('E_MISSING_FILE', lambda: h.lint(self.root, self.m))

    def test_broken_rule_ref(self):
        self.m['routes'][0]['rule_refs'] = ['NO-SUCH-RULE']
        self.error('E_REF', lambda: h.lint(self.root, self.m))

    def test_broken_owner_ref(self):
        self.m['rules'][0]['owner'] = 'nobody'
        self.error('E_REF', lambda: h.lint(self.root, self.m))

    def test_broken_executor_ref(self):
        self.m['rules'][0]['executor_refs'] = ['nobody']
        self.error('E_REF', lambda: h.lint(self.root, self.m))

    def test_orphan_rule_rejected(self):
        rule = copy.deepcopy(self.m['rules'][0]); rule['id'] = 'ORPHAN'
        self.m['rules'].append(rule)
        self.error('E_ORPHAN_RULE', lambda: h.lint(self.root, self.m))

    def test_extra_route_check_rejected(self):
        self.m['routes'][0]['evidence_refs'].append('unowned-check')
        self.error('E_ORPHAN_CHECK', lambda: h.lint(self.root, self.m))

    def test_incomplete_route_closure(self):
        self.m['routes'][0]['executor_refs'] = []
        self.error('E_REF_CLOSURE', lambda: h.lint(self.root, self.m))

    def test_unmatched_route_reported(self):
        self.t = h.load(self.root, 'tasks/plugin.json', 'task')
        self.assertEqual(h.resolve(self.root, self.m, self.t)['unmatched_routes'], ['route.app', 'route.web'])

    def test_no_route_blocks(self):
        self.t['tasks'] = ['unknown']
        self.assertEqual(h.resolve(self.root, self.m, self.t)['errors'][0]['code'], 'E_UNROUTED')

    def test_glob_segment_semantics(self):
        for path, pattern, expected in [('src/a', 'src/**', True), ('src/a/b', 'src/*', False), ('a.py', '**/*.py', True), ('src/a.py', '**/*.py', True), ('source/a', 'src/**', False), ('src/a', 'src/?', True), ('A/a', 'a/**', False)]:
            with self.subTest(path=path, pattern=pattern):
                self.assertEqual(h.glob_match(path, pattern), expected)

    def test_task_or_path_mode(self):
        route = self.m['routes'][0]
        route['match']['mode'] = 'task-or-path'
        self.t['tasks'] = ['bugfix']
        self.assertTrue(h.route_matches(route, self.t))
        route['match']['platforms'] = ['ios']
        self.assertFalse(h.route_matches(route, self.t))

    def test_task_or_path_coverage_symmetric(self):
        route = self.m['routes'][0]
        self.m['routes'] = [route]
        self.m['rules'] = [self.m['rules'][0]]
        route['match'].update(tasks=['build'], paths=['src/**'], platforms=[], domains=[], effects=[], mode='task-or-path')
        for tasks, paths in [(['bugfix'], ['src/a.txt']), (['build'], ['other/a.txt'])]:
            with self.subTest(tasks=tasks, paths=paths):
                self.t.update(tasks=tasks, paths=paths, approved_paths=['**'])
                self.assertEqual(h.resolve(self.root, self.m, self.t)['status'], 'pass')
        self.t.update(tasks=['bugfix'], paths=['other/a.txt'])
        self.assertEqual(h.resolve(self.root, self.m, self.t)['status'], 'blocked')

    def test_task_or_path_preserves_other_dimension_coverage(self):
        route = self.m['routes'][0]
        self.m['routes'] = [route]
        self.m['rules'] = [self.m['rules'][0]]
        route['match'].update(tasks=['build'], paths=['src/**'], platforms=[], domains=[], effects=[], mode='task-or-path')
        self.t.update(tasks=['bugfix'], paths=['src/a.txt'], approved_paths=['**'])
        self.t['effects'] = ['observe']
        for dimension in ('platforms', 'domains', 'effects'):
            with self.subTest(dimension=dimension):
                route['match'][dimension] = [self.t[dimension][0]]
                self.t[dimension].append('uncovered')
                result = h.resolve(self.root, self.m, self.t)
                self.assertIn('$/'+dimension, [e['path'] for e in result['errors'] if e['code'] == 'E_UNCOVERED_DIMENSION'])
                self.t[dimension].pop()
                route['match'][dimension] = []

    def test_literal_brackets_in_file_and_task_paths(self):
        page = self.root / 'pages/[policy].md'
        page.write_text('literal bracket context', encoding='utf-8')
        self.m['routes'][0]['context_set']['required'].append('pages/[policy].md')
        self.t['paths'].append('src/plugin/[id].tsx')
        self.assertEqual(h.resolve(self.root, self.m, self.t)['status'], 'pass')
        self.assertEqual(h.safe(self.root, 'pages/[policy].md', '$test'), page.resolve())
        self.assertTrue(h.glob_match('src/[id].tsx', 'src/[id].tsx'))
        self.assertFalse(h.glob_match('src/i.tsx', 'src/[id].tsx'))
        for value in ('src/*.tsx', 'src/?.tsx'):
            self.error('E_PATH', lambda: h.safe(self.root, value, '$test', must_exist=False))

    def test_scope_dimensions_and_exclusions(self):
        scope = self.m['rules'][0]['scope']
        self.assertTrue(h.scope_applies(scope, self.t))
        for key, value in [('actions', ['read']), ('tasks', ['other']), ('platforms', ['ios']), ('lifecycle', 'other')]:
            task = copy.deepcopy(self.t); task[key] = value
            self.assertFalse(h.scope_applies(scope, task), key)
        scope['exclusions'] = ['src/plugin/**']
        self.assertFalse(h.scope_applies(scope, self.t))

    def test_scope_multivalues_are_or(self):
        self.t['actions'] = ['read', 'edit']; self.t['platforms'] = ['plugin', 'ios']
        self.assertTrue(h.scope_applies(self.m['rules'][0]['scope'], self.t))

    def test_approved_paths_not_prefix(self):
        self.t['approved_paths'] = ['src/plugin']
        result = h.resolve(self.root, self.m, self.t)
        self.assertIn('E_OUT_OF_SCOPE', [e['code'] for e in result['errors']])
        self.assertEqual(result['stopped_actions'], ['edit'])

    def test_cross_scope_conflict_stops_only_affected_action(self):
        self.t['actions'] = ['edit', 'read']
        second = self.m['rules'][1]
        second['scope'] = copy.deepcopy(self.m['rules'][0]['scope'])
        second['constraints'][0]['value'] = 'disable'
        result = h.resolve(self.root, self.m, self.t)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['stopped_actions'], ['edit'])
        self.assertEqual(result['conflicts'][0]['rules'], ['PLUGIN-VERIFY', 'WEB-VERIFY'])

    def test_nonoverlap_constraints_do_not_conflict(self):
        self.m['rules'][1]['constraints'][0]['value'] = 'disable'
        self.assertEqual(h.resolve(self.root, self.m, self.t)['conflicts'], [])

    def test_path_escape_rejected(self):
        for path in ('../outside', '/tmp/outside', 'C:/outside', 'pages/../outside', 'pages\\outside', 'pages//outside', './pages/core.md'):
            with self.subTest(path=path):
                self.error('E_PATH', lambda: h.safe(self.root, path, '$test'))

    def test_symlink_escape_rejected(self):
        outside = Path(self.tmp.name) / 'outside.txt'; outside.write_text('secret', encoding='utf-8')
        link = self.root / 'escape.txt'
        try:
            link.symlink_to(outside)
        except OSError as exc:
            self.skipTest('symlink creation unavailable: ' + str(exc))
        self.error('E_PATH_ESCAPE', lambda: h.safe(self.root, 'escape.txt', '$test'))

    def test_artifact_bytes_verified(self):
        (self.root / 'artifacts/fixture.txt').write_text('changed', encoding='utf-8')
        self.error('E_ARTIFACT_DIGEST', lambda: h.resolve(self.root, self.m, self.t))

    def test_concrete_target_required(self):
        self.t['target']['id'] = 'latest'
        self.error('E_TARGET', lambda: h.resolve(self.root, self.m, self.t))

    def test_routing_digest_is_deterministic_and_changes(self):
        a = h.resolve(self.root, self.m, self.t)['routing_digest']
        reordered = dict(reversed(list(self.t.items())))
        self.assertEqual(a, h.resolve(self.root, self.m, reordered)['routing_digest'])
        self.t['source']['dirty_digest'] = 'a' * 64
        self.assertNotEqual(a, h.resolve(self.root, self.m, self.t)['routing_digest'])

    def test_demo_evidence_remains_not_run(self):
        self.assertEqual(self.checked()['status'], 'not-run')

    def test_current_envelope_positive(self):
        self.passing()
        result = self.checked()
        self.assertEqual(result['status'], 'pass')
        self.assertTrue(all(r['enforcement'] == 'proposed' for r in result['records']))

    def test_expired_pass_invalidated(self):
        self.passing()
        self.b['records'][0]['valid_until'] = '2026-11-14T09:30:00Z'
        result = self.checked()
        self.assertEqual(result['status'], 'not-run')
        self.assertEqual(result['records'][0]['historical_status'], 'pass')
        self.assertIn('expired', result['records'][0]['invalidation_reasons'])

    def test_source_environment_target_bindings(self):
        self.passing()
        original = copy.deepcopy(self.t)
        for key, field, value in [('source', 'commit', 'changed-commit'), ('source', 'dirty_digest', 'a' * 64), ('environment', 'config_digest', 'b' * 64), ('environment', 'permissions_digest', 'c' * 64), ('target', 'id', 'other-instance')]:
            with self.subTest(key=key, field=field):
                self.t = copy.deepcopy(original); self.t[key][field] = value
                result = self.checked()
                self.assertEqual(result['status'], 'not-run')
                self.assertIn(key + '-changed', result['records'][0]['invalidation_reasons'])

    def test_rule_and_executor_versions_invalidate(self):
        self.passing()
        self.m['rules'][0]['revision'] = 2
        self.m['executors'][0]['version'] = '2'
        result = self.checked()
        self.assertIn('rule-revision-changed', result['records'][0]['invalidation_reasons'])
        self.assertIn('executor-version-changed', result['records'][0]['invalidation_reasons'])

    def test_scope_changes_invalidate(self):
        self.passing()
        self.m['rules'][0]['scope']['tasks'].append('bugfix')
        self.assertIn('scope-changed', self.checked()['records'][0]['invalidation_reasons'])

    def test_future_collection_invalidates(self):
        self.passing()
        self.b['records'][0]['collected_at'] = '2026-11-14T11:00:00Z'
        self.assertIn('not-yet-valid', self.checked()['records'][0]['invalidation_reasons'])

    def test_invalid_validity_rejected(self):
        self.b['records'][0]['valid_until'] = '2026-11-14T08:00:00Z'
        self.error('E_VALIDITY', self.checked)

    def test_timezone_required(self):
        self.b['records'][0]['collected_at'] = '2026-11-14T09:00:00'
        self.error('E_TIME', self.checked)

    def test_missing_invalidation_trigger(self):
        self.b['records'][0]['invalidation_triggers'].remove('target')
        self.error('E_VALIDITY', self.checked)

    def test_missing_records_are_not_run(self):
        self.b['records'] = []
        result = self.checked()
        self.assertEqual(result['status'], 'not-run')
        self.assertEqual(len(result['records']), 3)

    def test_duplicate_records_rejected(self):
        self.b['records'].append(copy.deepcopy(self.b['records'][0]))
        self.error('E_DUPLICATE_ID', self.checked)

    def test_unknown_evidence_check_rejected(self):
        self.b['records'][0]['check_id'] = 'other-check'
        self.error('E_REF', self.checked)

    def test_fake_pass_not_executed_rejected(self):
        self.b['records'][0]['status'] = 'pass'
        self.error('E_FAKE_PASS', self.checked)

    def test_fake_pass_nonzero_exit_rejected(self):
        self.passing(); self.b['records'][0]['execution']['exit_code'] = 1
        self.error('E_FAKE_PASS', self.checked)

    def test_fake_pass_simulated_target_rejected(self):
        self.passing(); self.b['records'][0]['target']['simulated'] = True
        self.error('E_FAKE_PASS', self.checked)

    def test_schema_executor_cannot_prove_product_pass(self):
        self.passing(); self.m['executors'][0]['kind'] = 'schema'
        self.error('E_FAKE_PASS', self.checked)

    def test_pass_needs_artifact(self):
        self.passing(); self.b['records'][0]['artifacts'] = []
        self.error('E_FAKE_PASS', self.checked)

    def test_na_for_applicable_rule_rejected(self):
        record = self.b['records'][0]
        record['status'] = 'not-applicable'
        record['na_basis'] = {'reason': 'no environment is not an excuse', 'scope_dimension': 'platforms', 'excluded_values': self.t['platforms']}
        self.error('E_NA_SCOPE', self.checked)

    def test_valid_na_for_excluded_scope(self):
        self.t = h.load(self.root, 'tasks/plugin.json', 'task')
        for rule in self.m['rules']:
            rule['scope']['lifecycle'] = ['release']
        for record, rule in zip(self.b['records'], self.m['rules']):
            record['scope'] = copy.deepcopy(rule['scope'])
            record['status'] = 'not-applicable'
            record['na_basis'] = {'reason': 'development is outside release-only rule', 'scope_dimension': 'lifecycle', 'excluded_values': ['development']}
        self.assertEqual(self.checked()['status'], 'not-applicable')

    def test_na_requires_matching_exclusion_dimension(self):
        self.m['rules'][0]['scope']['lifecycle'] = ['release']
        record = self.b['records'][0]
        record['status'] = 'not-applicable'
        record['na_basis'] = {'reason': 'wrong dimension', 'scope_dimension': 'platforms', 'excluded_values': self.t['platforms']}
        self.error('E_NA_SCOPE', self.checked)

    def test_aggregate_precedence(self):
        self.assertEqual(h.aggregate(['pass', 'not-applicable']), 'pass')
        self.assertEqual(h.aggregate(['pass', 'not-run']), 'not-run')
        self.assertEqual(h.aggregate(['not-run', 'blocked']), 'blocked')
        self.assertEqual(h.aggregate(['blocked', 'fail']), 'fail')
        self.assertEqual(h.aggregate(['not-applicable']), 'not-applicable')

    def test_cli_lint_exit_zero(self):
        code, result = self.cli('lint')
        self.assertEqual(code, 0); self.assertEqual(result['status'], 'pass')

    def test_cli_resolve_exit_two_on_unknown(self):
        self.t['facts'] = {}
        (self.root / 'tasks/unknown.json').write_text(json.dumps(self.t), encoding='utf-8')
        code, result = self.cli('resolve', '--task', 'tasks/unknown.json')
        self.assertEqual(code, 2); self.assertEqual(result['status'], 'blocked')

    def test_cli_evidence_exit_two_not_run(self):
        code, result = self.cli('evidence', '--task', 'tasks/hybrid.json', '--records', 'evidence/records.json', '--now', '2026-11-14T10:00:00Z')
        self.assertEqual(code, 2); self.assertEqual(result['status'], 'not-run')

    def test_cli_invalid_exit_one(self):
        (self.root / 'bad.json').write_text('{}', encoding='utf-8')
        code, result = self.cli('lint', '--manifest', 'bad.json')
        self.assertEqual(code, 1); self.assertEqual(result['errors'][0]['code'], 'E_REQUIRED')

    def test_cli_isolated_surrogates_exit_one_json(self):
        for bad in ('\ud800', '\udfff'):
            for position in ('value', 'key'):
                with self.subTest(codepoint=ord(bad), position=position):
                    task = copy.deepcopy(self.t)
                    if position == 'value':
                        task['change_id'] = bad
                    else:
                        task['facts'][bad] = True
                    (self.root / 'tasks/unicode.json').write_text(json.dumps(task), encoding='utf-8')
                    code, result = self.cli('resolve', '--task', 'tasks/unicode.json')
                    self.assertEqual(code, 1)
                    self.assertEqual(result['errors'][0]['code'], 'E_UNICODE')

    def test_json_chinese_emoji_and_valid_surrogate_pair(self):
        self.t['change_id'] = '变更😀'
        path = self.root / 'tasks/unicode.json'
        # ensure_ascii emits a valid surrogate pair for the emoji; decoder joins it.
        path.write_text(json.dumps(self.t), encoding='utf-8')
        self.assertEqual(h.read_json(path)['change_id'], '变更😀')
        code, result = self.cli('resolve', '--task', 'tasks/unicode.json')
        self.assertEqual(code, 0)
        self.assertEqual(len(result['routing_digest']), 64)

    def test_duplicate_surrogate_keys_are_unicode_error(self):
        path = self.root / 'surrogates.json'
        key = json.dumps(chr(0xd800))
        path.write_text('{' + key + ':1,' + key + ':2}', encoding='utf-8')
        self.error('E_UNICODE', lambda: h.read_json(path))

    def test_cli_missing_root_exit_three(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = h.main(['lint', '--root', str(self.root / 'does-not-exist')])
        self.assertEqual(code, 3)

    def test_no_manifest_shell_execution(self):
        self.passing()
        marker = self.root / 'NEVER-CREATED'
        for r in self.b['records']:
            r['execution']['command'] = 'python -c "open(\"' + str(marker) + '\", \"w\")"'
        self.assertEqual(self.checked()['status'], 'pass')
        self.assertFalse(marker.exists())

    def test_cli_is_read_only(self):
        before = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.cli('resolve', '--task', 'tasks/hybrid.json')
        self.cli('evidence', '--task', 'tasks/hybrid.json', '--records', 'evidence/records.json', '--now', '2026-11-14T10:00:00Z')
        after = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_unsupported_schema_keyword_rejected(self):
        self.error('E_SCHEMA_KEYWORD', lambda: h.validate({}, {'type': 'object', 'oneOf': []}))

    def test_hidden_optional_schema_keyword_rejected(self):
        self.error('E_SCHEMA_KEYWORD', lambda: h.validate({}, {'type': 'object', 'properties': {'absent': {'type': 'string', 'unknownKeyword': True}}}))

    def test_hidden_items_schema_keyword_rejected(self):
        self.error('E_SCHEMA_KEYWORD', lambda: h.validate([], {'type': 'array', 'items': {'type': 'string', 'unknownKeyword': True}}))

    def test_hidden_additional_schema_keyword_rejected(self):
        self.error('E_SCHEMA_KEYWORD', lambda: h.validate({}, {'type': 'object', 'additionalProperties': {'unknownKeyword': True}}))

    def test_invalid_schema_type_rejected(self):
        self.error('E_SCHEMA', lambda: h.validate(None, {'type': 'number'}))

    def test_malformed_hidden_schema_operands_rejected(self):
        malformed = [{'properties': []}, {'required': 'x'}, {'type': []}, {'type': ['string', 'string']}, {'minItems': True}, {'minLength': -1}, {'uniqueItems': 1}, {'minimum': False}, {'enum': []}, {'pattern': '['}, {'description': 42}, {'additionalProperties': 0}]
        for bad in malformed:
            with self.subTest(schema=bad):
                self.error('E_SCHEMA', lambda: h.validate({}, {'type': 'object', 'properties': {'absent': bad}}))

    def test_valid_absent_schema_branches(self):
        h.validate({}, {'type': 'object', 'properties': {'absent': {'type': ['string', 'null'], 'minLength': 1}}, 'additionalProperties': {'type': 'integer', 'minimum': 0}})
        h.validate([], {'type': 'array', 'items': {'type': 'string', 'pattern': '^ok$'}})

    def test_extra_route_executor_rejected(self):
        self.m['executors'].append({'id': 'unused', 'version': '1', 'kind': 'manual'})
        self.m['routes'][0]['executor_refs'].append('unused')
        self.error('E_ORPHAN_EXECUTOR', lambda: h.lint(self.root, self.m))

    def test_diff_expansion_requires_reroute(self):
        self.t['paths'].append('unmapped/new.txt')
        self.t['approved_paths'].append('unmapped/**')
        result = h.resolve(self.root, self.m, self.t)
        self.assertIn('E_UNCOVERED_DIMENSION', [e['code'] for e in result['errors']])
        self.assertEqual(result['status'], 'blocked')

    def test_new_platform_requires_reroute(self):
        self.t['platforms'].append('unknown-platform')
        self.assertEqual(h.resolve(self.root, self.m, self.t)['status'], 'blocked')

    def test_paths_and_facts_changes_invalidate_pass(self):
        self.passing()
        self.t['paths'].append('src/plugin/other.txt')
        self.t['facts']['changes_persistence'] = False
        result = self.checked()
        self.assertEqual(result['status'], 'not-run')
        self.assertIn('routing-changed', result['records'][0]['invalidation_reasons'])

    def test_context_page_change_invalidates_pass(self):
        self.passing()
        (self.root / 'pages/core.md').write_text('updated acceptance contract', encoding='utf-8')
        result = self.checked()
        self.assertEqual(result['status'], 'not-run')
        self.assertIn('routing-changed', result['records'][0]['invalidation_reasons'])

    def test_duplicate_artifact_path_rejected(self):
        artifact = copy.deepcopy(self.t['artifacts'][0]); artifact['sha256'] = 'a' * 64
        self.t['artifacts'].append(artifact)
        self.error('E_DUPLICATE', lambda: h.resolve(self.root, self.m, self.t))

    def test_resolved_escape_guard_without_native_symlink(self):
        from unittest.mock import patch
        outside = Path(self.tmp.name) / 'outside.txt'
        with patch.object(Path, 'resolve', return_value=outside):
            self.error('E_PATH_ESCAPE', lambda: h.safe(self.root, 'escape.txt', '$test', must_exist=False))

if __name__ == '__main__':
    unittest.main()
