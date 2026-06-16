"""Tests for user CRUD endpoints — list/create/update/delete/reset-password."""
import pytest
from apps.rbac.models import User, UserRole


# ── LIST ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_list_users(authed_client):
    """GET /api/rbac/users/ → 200 + pagination 格式。"""
    client, _ = authed_client
    resp = client.get('/api/rbac/users/')
    assert resp.status_code == 200
    assert 'data' in resp.data
    assert 'pagination' in resp.data
    assert 'total' in resp.data['pagination']


@pytest.mark.django_db
def test_list_users_pagination(authed_client):
    """带分页参数 → 正确分页。"""
    client, _ = authed_client
    resp = client.get('/api/rbac/users/', {'page': 1, 'page_size': 10})
    assert resp.status_code == 200
    assert resp.data['pagination']['page'] == 1
    assert resp.data['pagination']['page_size'] == 10


@pytest.mark.django_db
def test_list_users_search(authed_client, normal_user):
    """带 search 参数 → 返回匹配结果。"""
    client, _ = authed_client
    resp = client.get('/api/rbac/users/', {'search': 'admin'})
    assert resp.status_code == 200
    usernames = [u['username'] for u in resp.data['data']]
    assert 'admin' in usernames


@pytest.mark.django_db
def test_list_users_search_no_match(authed_client):
    """search 无匹配 → 返回空列表。"""
    client, _ = authed_client
    resp = client.get('/api/rbac/users/', {'search': 'nonexistent'})
    assert resp.status_code == 200
    assert len(resp.data['data']) == 0


# ── CREATE ───────────────────────────────────────────────

@pytest.mark.django_db
def test_create_user(authed_client, user_role):
    """POST 创建用户 → 201。"""
    client, _ = authed_client
    data = {
        'username': 'newuser',
        'email': 'new@test.com',
        'password': 'pass123',
        'role_ids': [user_role.id],
    }
    resp = client.post('/api/rbac/users/', data, format='json')
    assert resp.status_code == 201
    assert resp.data['data']['username'] == 'newuser'
    # 验证用户已存入 DB
    assert User.objects.filter(username='newuser').exists()


@pytest.mark.django_db
def test_create_user_minimal(authed_client):
    """最简参数创建用户（不含角色）。"""
    client, _ = authed_client
    resp = client.post('/api/rbac/users/', {
        'username': 'minimal',
        'email': 'min@test.com',
        'password': 'pass123',
    }, format='json')
    assert resp.status_code == 201


@pytest.mark.django_db
def test_create_user_duplicate_username(authed_client, root_user):
    """重复用户名 → 409 + DUPLICATE_USERNAME。"""
    client, _ = authed_client
    resp = client.post('/api/rbac/users/', {
        'username': 'admin',
        'email': 'other@test.com',
        'password': 'pass123',
    }, format='json')
    assert resp.status_code == 409
    assert resp.data['error']['code'] == 'DUPLICATE_USERNAME'


@pytest.mark.django_db
def test_create_user_duplicate_email(authed_client, root_user):
    """重复邮箱 → 409 + DUPLICATE_EMAIL。"""
    client, _ = authed_client
    resp = client.post('/api/rbac/users/', {
        'username': 'another',
        'email': 'admin@test.com',
        'password': 'pass123',
    }, format='json')
    assert resp.status_code == 409
    assert resp.data['error']['code'] == 'DUPLICATE_EMAIL'


@pytest.mark.django_db
def test_create_user_as_normal_user(normal_client):
    """普通用户创建 → 403。"""
    client, _ = normal_client
    resp = client.post('/api/rbac/users/', {
        'username': 'hacker', 'email': 'hack@test.com', 'password': 'pass123',
    }, format='json')
    assert resp.status_code == 403


# ── RETRIEVE ─────────────────────────────────────────────

@pytest.mark.django_db
def test_get_user_detail(authed_client, normal_user):
    """GET /api/rbac/users/{id}/ → 200。"""
    client, _ = authed_client
    resp = client.get(f'/api/rbac/users/{normal_user.id}/')
    assert resp.status_code == 200
    assert resp.data['data']['username'] == 'user001'


@pytest.mark.django_db
def test_get_user_not_found(authed_client):
    """不存在的用户 → 404。"""
    client, _ = authed_client
    resp = client.get('/api/rbac/users/99999/')
    assert resp.status_code == 404


# ── UPDATE ───────────────────────────────────────────────

@pytest.mark.django_db
def test_update_user(authed_client, normal_user):
    """PUT 更新用户 → 200 + 字段已更新。"""
    client, _ = authed_client
    resp = client.put(f'/api/rbac/users/{normal_user.id}/', {
        'username': 'updated_user',
        'email': 'updated@test.com',
    }, format='json')
    assert resp.status_code == 200
    assert resp.data['data']['username'] == 'updated_user'
    assert resp.data['data']['email'] == 'updated@test.com'


@pytest.mark.django_db
def test_update_user_not_found(authed_client):
    """更新不存在的用户 → 404。"""
    client, _ = authed_client
    resp = client.put('/api/rbac/users/99999/', {
        'username': 'ghost',
    }, format='json')
    assert resp.status_code == 404


# ── DELETE ───────────────────────────────────────────────

@pytest.mark.django_db
def test_delete_user(authed_client, normal_user):
    """DELETE 软删除用户 → 204 + 用户不可见。"""
    client, _ = authed_client
    resp = client.delete(f'/api/rbac/users/{normal_user.id}/')
    assert resp.status_code == 204

    # 验证已软删除
    user = User.objects.with_deleted().get(id=normal_user.id)
    assert user.is_deleted is True

    # 默认查询不可见
    assert not User.objects.filter(id=normal_user.id).exists()


@pytest.mark.django_db
def test_delete_user_not_found(authed_client):
    """删除不存在的用户 → 404。"""
    client, _ = authed_client
    resp = client.delete('/api/rbac/users/99999/')
    assert resp.status_code == 404


# ── RESET PASSWORD ───────────────────────────────────────

@pytest.mark.django_db
def test_reset_password(authed_client, normal_user):
    """重置密码 → 200 + 新密码可登录。"""
    client, _ = authed_client
    resp = client.post(f'/api/rbac/users/{normal_user.id}/reset-password/', {
        'password': 'newpass456',
    }, format='json')
    assert resp.status_code == 200

    # 验证新密码可用
    from django.contrib.auth import authenticate
    refreshed = authenticate(username='user001', password='newpass456')
    assert refreshed is not None
