"""
Django base settings.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-vue-adminx-dev-insecure-key')

DEBUG = False

ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 第三方
    'rest_framework',
    'corsheaders',
    'django_filters',
    # 项目应用
    'apps.common',
    'apps.rbac',
    'apps.audit',
    'apps.ai',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_USER_MODEL = 'rbac.User'

AUTHENTICATION_BACKENDS = [
    'apps.rbac.backends.UserBackend',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Session
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

# CORS - dev overrides this
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = []


# ── AI 集成配置 ────────────────────────────────────────────────────
# 多 Provider 列表按优先级排序，故障自动切换 (N+1 容灾)
AI_PROVIDERS = [
    {
        'name': 'openai',
        'api_key': os.environ.get('OPENAI_API_KEY', ''),
        'base_url': os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
        'model': os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
    },
    {
        'name': 'deepseek',
        'api_key': os.environ.get('DEEPSEEK_API_KEY', ''),
        'base_url': os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
        'model': os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat'),
    },
    {
        'name': 'qclaw',
        'api_key': os.environ.get('QCLAW_API_KEY', ''),
        'base_url': os.environ.get('QCLAW_BASE_URL', 'https://api.qclaw.ai/v1'),
        'model': os.environ.get('QCLAW_MODEL', 'pool-deepseek-v4-pro'),
    },
]

# 故障转移
AI_FAILOVER_FAILURE_THRESHOLD = int(os.environ.get('AI_FAILOVER_FAILURE_THRESHOLD', '3'))
AI_FAILOVER_RECOVERY_TIMEOUT = int(os.environ.get('AI_FAILOVER_RECOVERY_TIMEOUT', '60'))
AI_FAILOVER_ALERT_CHANNEL = os.environ.get('AI_FAILOVER_ALERT_CHANNEL', 'notification')
AI_FAILOVER_ALERT_WEBHOOK = os.environ.get('AI_FAILOVER_ALERT_WEBHOOK', '')

# 审批流
AI_APPROVAL_ENABLED = os.environ.get('AI_APPROVAL_ENABLED', 'true').lower() == 'true'
AI_APPROVAL_AUTO_EXECUTE = os.environ.get('AI_APPROVAL_AUTO_EXECUTE', 'true').lower() == 'true'
AI_APPROVAL_TIMEOUT_HOURS = int(os.environ.get('AI_APPROVAL_TIMEOUT_HOURS', '24'))

# 调用限制
AI_RATE_LIMIT_PER_ROOT = int(os.environ.get('AI_RATE_LIMIT_PER_ROOT', '100'))
AI_RATE_LIMIT_PER_AGENT = int(os.environ.get('AI_RATE_LIMIT_PER_AGENT', '20'))
AI_TIMEOUT = int(os.environ.get('AI_TIMEOUT', '30'))

# 审计
AI_AUDIT_RETENTION_DAYS = int(os.environ.get('AI_AUDIT_RETENTION_DAYS', '90'))

# Agent Token 签发密钥（root 为 Agent 授权时使用）
AI_AGENT_TOKEN_SECRET = os.environ.get('AI_AGENT_TOKEN_SECRET', SECRET_KEY)

# 模拟模式 — 未配置任何 Provider Key 时启用，返回本地占位回复
AI_MOCK_WHEN_NO_KEY = os.environ.get('AI_MOCK_WHEN_NO_KEY', 'true').lower() == 'true'
