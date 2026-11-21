"""Read-only legacy source reproduction using an isolated temporary SQLite database."""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('--source', required=True)
p.add_argument('--output', required=True)
a = p.parse_args()
sys.path.insert(0, str(Path(a.source).resolve() / 'backend'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'
from django.conf import settings
with tempfile.TemporaryDirectory(prefix='ram-legacy-token-') as tmp:
    settings.DATABASES['default']['NAME'] = str(Path(tmp) / 'isolated.sqlite3')
    settings.AI_PROVIDERS = []
    settings.AI_FAILOVER_ALERT_WEBHOOK = ''
    settings.AI_AGENT_TOKEN_SECRET = 'synthetic-ephemeral-legacy-test-' + os.urandom(16).hex()
    import django
    django.setup()
    from django.core.management import call_command
    from django.db import connections
    from apps.rbac.models import User, Role, UserRole
    from apps.ai.permissions import AgentTokenService
    from unittest.mock import patch
    call_command('migrate', verbosity=0, interactive=False)
    issuer = User.objects.create_user(username='legacy_synthetic', email='legacy@example.invalid', password=None)
    role = Role.objects.create(code='root', name='synthetic-root')
    link = UserRole.objects.create(user=issuer, role=role)
    with patch('apps.ai.permissions.time.time', return_value=1800000000):
        token = AgentTokenService.issue(root_user_id=issuer.id, agent_id='synthetic-agent')
        duplicate = AgentTokenService.issue(root_user_id=issuer.id, agent_id='synthetic-agent')
        issuer.is_active = False
        issuer.save(update_fields=['is_active'])
        disabled_accepted = AgentTokenService.verify(token) is not None
        link.delete()
        removed_role_accepted = AgentTokenService.verify(token) is not None
    result = {'legacy_source': str(Path(a.source).resolve()), 'django': django.get_version(), 'isolated_database': True, 'token_material_persisted': False, 'observations': {'same_second_duplicate': token == duplicate, 'disabled_issuer_accepted': disabled_accepted, 'removed_root_role_accepted': removed_role_accepted}, 'expected_vulnerabilities_reproduced': disabled_accepted and removed_role_accepted}
    Path(a.output).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    connections.close_all()
    assert result['expected_vulnerabilities_reproduced']
