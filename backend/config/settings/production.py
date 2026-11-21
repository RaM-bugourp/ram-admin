"""Explicit production boundary; local verification is not deployment acceptance."""
from .base import *
from django.core.exceptions import ImproperlyConfigured

secret=os.environ.get('DJANGO_SECRET_KEY','')
if len(secret)<50 or len(set(secret))<12 or 'insecure' in secret.lower():
    raise ImproperlyConfigured('Production requires an explicit strong DJANGO_SECRET_KEY (50+ characters)')
SECRET_KEY=secret
ALLOWED_HOSTS=[x.strip() for x in os.environ.get('DJANGO_ALLOWED_HOSTS','').split(',') if x.strip()]
if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:raise ImproperlyConfigured('Production requires explicit DJANGO_ALLOWED_HOSTS without wildcard')
database=os.environ.get('DJANGO_DB_PATH','')
if not database or not Path(database).is_absolute():raise ImproperlyConfigured('Production requires an explicit absolute DJANGO_DB_PATH')
DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':database}}
DEBUG=False
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
X_FRAME_OPTIONS='DENY'
CORS_ALLOW_ALL_ORIGINS=False
AI_MOCK_WHEN_NO_KEY=False
# TLS termination/proxy trust intentionally not guessed; deployment owner must configure.
