"""
WSGI config — 生产环境使用
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ram_admin.settings')
application = get_wsgi_application()
