"""Build project-owned Harness manifest; never edits the frozen vendor payload."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def write(path, value):
    (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def main():
    owners = [{'id': 'dev', 'contact': 'session:ram-harness-dev', 'backup': 'session:lead'}, {'id': 'lead', 'contact': 'session:lead', 'backup': 'user-via-lead'}]
    executors = [{'id': 'verify', 'version': '1', 'kind': 'automated'}]
    rules, routes = [], []
    common = ['AGENTS.md', 'docs/harness/PLAN.md', 'docs/harness/OWNERS.md', 'docs/harness/BRIDGE.md', 'docs/harness/ROUTING.md']
    common += ['docs/harness/TASK-TOKEN-001.md']
    common += ['docs/harness/vendor/1.0.0/docs/' + p for p in ['START-HERE.md','overview.md','adoption.md','routing.md','ownership.md','pr-boundaries.md','test-boundaries.md','evidence.md','task-lifecycle.md','capabilities.md','platforms/README.md','platforms/selection.md','platforms/evidence.md','platforms/web/README.md','platforms/web/verify.md']]
    for name, tasks, page, check in [
        ('SCOPE', ['fix', 'feature'], 'pr-boundaries.md', 'product-tests'),
        ('API', ['api', 'security'], 'platforms/web/api-config.md', 'product-tests'),
        ('DATA', ['data'], 'platforms/web/data.md', 'migration-tests'),
        ('UI', ['ui'], 'platforms/web/frontend.md', 'frontend-build'),
        ('BUILD', ['build'], 'test-boundaries.md', 'frontend-build'),
        ('DOC', ['docs'], 'adoption.md', 'harness-routing'),
        ('RELEASE', ['release'], 'platforms/web/operations.md', 'deployment'),
    ]:
        rid = f'RAM-{name}-001'
        source = 'docs/harness/vendor/1.0.0/docs/' + page
        rules.append({'id': rid, 'revision': 1, 'owner': 'dev', 'scope': {'actions': ['*'], 'paths': ['**'], 'platforms': ['*'], 'tasks': tasks, 'lifecycle': ['*'], 'exclusions': []}, 'source': source, 'statement': f'Apply {name} context and original acceptance without weakening scope.', 'enforcement': 'advisory', 'executor_refs': ['verify'], 'evidence_refs': [check], 'constraints': []})
        routes.append({'id': 'route-' + name.lower(), 'owner': 'dev', 'match': {'tasks': tasks, 'paths': ['**'], 'platforms': ['*'], 'domains': ['*'], 'effects': ['*'], 'mode': 'all'}, 'context_set': {'required': list(dict.fromkeys(common + [source, 'docs/harness/vendor/1.0.0/docs/test-boundaries.md'])), 'conditional': [{'when': {'fact': 'has_frontend', 'equals': True}, 'add': ['docs/harness/vendor/1.0.0/docs/platforms/web/frontend.md']}, {'when': {'fact': 'has_database', 'equals': True}, 'add': ['docs/harness/vendor/1.0.0/docs/platforms/web/data.md', 'docs/harness/vendor/1.0.0/docs/platforms/web/operations.md']}]}, 'rule_refs': [rid], 'executor_refs': ['verify'], 'evidence_refs': [check]})
    for rule in rules:
        if rule['id'] == 'RAM-UI-001':
            rule['evidence_refs'].append('browser-e2e')
    for route in routes:
        if route['id'] == 'route-ui':
            route['evidence_refs'].append('browser-e2e')
    write('harness.json', {'schema_version': 1, 'project_id': 'ram-admin-0.2.0-harness.1', 'owners': owners, 'executors': executors, 'rules': rules, 'routes': routes})
if __name__ == '__main__':
    main()
