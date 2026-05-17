"""
pytest 配置文件
"""

import pytest
import os
import sys
from pathlib import Path

# 添加项目路径
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR.parent / 'packages'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ram_admin.settings')


@pytest.fixture
def admin_user(db):
    """创建管理员用户"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'is_superuser': True,
            'is_staff': True,
        }
    )
    user.set_password('admin123')
    user.save()
    return user


@pytest.fixture
def api_client():
    """DRF 测试客户端"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """已认证的测试客户端"""
    api_client.force_authenticate(user=admin_user)
    return api_client
