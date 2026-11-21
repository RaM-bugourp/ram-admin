"""Internal test child. Sensitive test-only input via stdin; never printed or stored."""
import json, os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
os.environ['DJANGO_SETTINGS_MODULE']='config.settings.test'
state=json.load(sys.stdin)
from django.conf import settings
settings.DATABASES['default']['NAME']=state['database']
settings.AI_AGENT_TOKEN_SECRET=state['secret']
import django
django.setup()
from apps.ai.permissions import AgentTokenService
from django.db import connections
accepted=AgentTokenService.verify(state['token']) is not None
connections.close_all()
assert accepted is state['expected_accepted'],'credential outcome mismatch (redacted)'
print(json.dumps({'accepted':accepted,'independent_process':True,'secret_or_token_output':False}))
