"""Tests for authentication endpoints — login/logout/csrf/user-info."""
import pytest
from django.urls import reverse
from apps.rbac.models import User, UserRole


# ── LOGIN ────────────────────────────────────────────────

@pytest.mark.django_db
def test_login_success(api_client, root_user, root_role):
    """正确用户名密码 → 200 + data + roles非空。"""
    resp = api_client.post('/api/auth/login/', {'username': 'admin', 'password': 'admin123'}, format='json')
    assert resp.status_code == 200
    data = resp.data.get('data')
    assert data is not None
    assert data['username'] == 'admin'
    assert len(data['roles']) > 0
    assert any(r['code'] == 'root' for r in data['roles'])


@pytest.mark.django_db
def test_login_failure_wrong_password(api_client, root_user):
    """错误密码 → 401 + error 格式。"""
    resp = api_client.post('/api/auth/login/', {'username': 'admin', 'password': 'wrong'}, format='json')
    assert resp.status_code == 401
    assert 'error' in resp.data
    assert resp.data['error']['code'] == 'INVALID_CREDENTIALS'


@pytest.mark.django_db
def test_login_failure_empty_credentials(api_client):
    """空用户名密码 → 400。"""
    resp = api_client.post('/api/auth/login/', {'username': '', 'password': ''}, format='json')
    assert resp.status_code == 400
    assert 'error' in resp.data


@pytest.mark.django_db
def test_login_inactive_user(api_client, root_user):
    """已禁用用户 → 403。"""
    root_user.is_active = False
    root_user.save()
    resp = api_client.post('/api/auth/login/', {'username': 'admin', 'password': 'admin123'}, format='json')
    assert resp.status_code == 403
    assert resp.data['error']['code'] == 'USER_INACTIVE'


@pytest.mark.django_db
def test_login_soft_deleted_user(api_client, root_user, root_role):
    """软删除用户 → 401（backends.py 应过滤 is_deleted）。"""
    root_user.soft_delete()
    resp = api_client.post('/api/auth/login/', {'username': 'admin', 'password': 'admin123'}, format='json')
    assert resp.status_code == 401
    assert resp.data['error']['code'] == 'INVALID_CREDENTIALS'


# ── CSRF ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_csrf_endpoint(api_client, root_user):
    """GET /api/auth/csrf/ → 设置 csrftoken Cookie。"""
    resp = api_client.get('/api/auth/csrf/')
    assert resp.status_code == 200
    assert 'csrftoken' in resp.cookies or 'csrf' in str(resp.cookies)


# ── USER-INFO ────────────────────────────────────────────

@pytest.mark.django_db
def test_user_info_authenticated(authed_client):
    """已登录用户 GET user-info → 返回 username/email/roles。"""
    client, user = authed_client
    resp = client.get('/api/auth/user-info/')
    assert resp.status_code == 200
    data = resp.data.get('data')
    assert data is not None
    assert data['username'] == 'admin'
    assert data['email'] == 'admin@test.com'
    assert len(data['roles']) > 0
    assert 'permissions' in data


@pytest.mark.django_db
def test_user_info_unauthenticated(api_client):
    """未登录用户 GET user-info → 403。"""
    resp = api_client.get('/api/auth/user-info/')
    assert resp.status_code == 403


# ── LOGOUT ───────────────────────────────────────────────

@pytest.mark.django_db
def test_logout(authed_client):
    """已登录用户登出 → 200。"""
    client, _ = authed_client
    resp = client.post('/api/auth/logout/')
    assert resp.status_code == 200
