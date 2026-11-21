"""Isolated tests only. No deployment secrets or application database are loaded."""
import secrets
from .base import *
SECRET_KEY = secrets.token_urlsafe(48)
AI_AGENT_TOKEN_SECRET = secrets.token_urlsafe(48)
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
AI_PROVIDERS = []
AI_FAILOVER_ALERT_WEBHOOK = ''
AI_APPROVAL_AUTO_EXECUTE = False
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
