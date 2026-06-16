"""Global test fixtures — shared across common/rbac/ai."""
import pytest
from rest_framework.test import APIClient
from apps.rbac.models import User, Role, UserRole


@pytest.fixture
def api_client():
    """DRF APIClient，不校验 CSRF."""
    return APIClient(enforce_csrf_checks=False)


@pytest.fixture
def root_role(db):
    return Role.objects.create(name='管理员', code='root')


@pytest.fixture
def boss_role(db):
    return Role.objects.create(name='BOSS', code='boss', description='全局唯一管理员', is_unique=True)


@pytest.fixture
def user_role(db):
    return Role.objects.create(name='普通用户', code='user')


@pytest.fixture
def root_user(db, root_role):
    """创建 root 角色 + root 用户."""
    user = User.objects.create_user(
        username='admin', email='admin@test.com', password='admin123',
    )
    UserRole.objects.create(user=user, role=root_role)
    return user


@pytest.fixture
def boss_user(db, boss_role):
    """创建 BOSS 角色 + BOSS 用户."""
    user = User.objects.create_user(
        username='boss001', email='boss@test.com', password='boss123',
    )
    UserRole.objects.create(user=user, role=boss_role)
    return user


@pytest.fixture
def normal_user(db, user_role):
    """创建普通用户."""
    user = User.objects.create_user(
        username='user001', email='user@test.com', password='user123',
    )
    UserRole.objects.create(user=user, role=user_role)
    return user


@pytest.fixture
def authed_client(api_client, root_user):
    """已登录 root 用户的 API client."""
    api_client.force_authenticate(user=root_user)
    return api_client, root_user


@pytest.fixture
def normal_client(api_client, normal_user):
    """已登录普通用户的 API client."""
    api_client.force_authenticate(user=normal_user)
    return api_client, normal_user


@pytest.fixture
def boss_client(api_client, boss_user):
    """已登录 BOSS 用户的 API client."""
    api_client.force_authenticate(user=boss_user)
    return api_client, boss_user
