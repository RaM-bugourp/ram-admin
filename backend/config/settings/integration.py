"""Loopback synthetic integration only. Never loads dev database or .env."""
from .base import *
from django.core.exceptions import ImproperlyConfigured
path=os.environ.get('RAM_TEST_DB','')
if not path or not Path(path).is_absolute() or '.tmp' not in Path(path).parts:raise ImproperlyConfigured('Integration requires root-local isolated .tmp database')
SECRET_KEY=os.environ.get('RAM_TEST_SECRET','')
if len(SECRET_KEY)<50:raise ImproperlyConfigured('Integration requires ephemeral process secret')
DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':path,'OPTIONS':{'timeout':20}}}
ALLOWED_HOSTS=['127.0.0.1','localhost','testserver']
AI_PROVIDERS=[]
AI_UI_ENABLED=False
AI_FAILOVER_ALERT_WEBHOOK=''
AI_AGENT_TOKEN_SECRET=os.environ.get('RAM_TEST_AGENT_SECRET','')
AI_APPROVAL_AUTO_EXECUTE=True
AI_MOCK_WHEN_NO_KEY=False
PASSWORD_HASHERS=['django.contrib.auth.hashers.PBKDF2PasswordHasher']
