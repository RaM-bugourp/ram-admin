"""Tests for role CRUD endpoints — list/create/update/delete + BOSS 唯一性."""
import pytest
from apps.rbac.models import Role, UserRole


# ── LIST ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_list_roles(authed_client, root_role, user_role, boss_role):
    """GET /api/rbac/roles/ → 200 + 列表。"""
    client, _ = authed_client
    resp = client.get('/api/rbac/roles/')
    assert resp.status_code == 200
    assert 'data' in resp.data
    codes = [r['code'] for r in resp.data['data']]
    assert 'root' in codes
    assert 'user' in codes
    assert 'boss' in codes


# ── CREATE ───────────────────────────────────────────────

@pytest.mark.django_db
def test_create_role(authed_client):
    """POST 创建角色 → 201。"""
    client, _ = authed_client
    resp = client.post('/api/rbac/roles/', {
        'name': '测试角色', 'code': 'test_role',
    }, format='json')
    assert resp.status_code == 201
    assert resp.data['data']['name'] == '测试角色'
    assert resp.data['data']['code'] == 'test_role'
    assert Role.objects.filter(code='test_role').exists()


@pytest.mark.django_db
def test_create_role_duplicate_name(authed_client, root_role):
    """重复角色名 → 409。"""
    client, _ = authed_client
    resp = client.post('/api/rbac/roles/', {
        'name': '管理员', 'code': 'admin2',
    }, format='json')
    assert resp.status_code == 409
    assert resp.data['error']['code'] == 'DUPLICATE_ROLE_NAME'


@pytest.mark.django_db
def test_create_role_duplicate_code(authed_client, root_role):
    """重复角色编码 → 409。"""
    client, _ = authed_client
    resp = client.post('/api/rbac/roles/', {
        'name': '管理员2', 'code': 'root',
    }, format='json')
    assert resp.status_code == 409
    assert resp.data['error']['code'] == 'DUPLICATE_ROLE_CODE'


@pytest.mark.django_db
def test_normal_user_cannot_create_role(normal_client):
    """普通用户创建角色 → 403。"""
    client, _ = normal_client
    resp = client.post('/api/rbac/roles/', {
        'name': '黑客', 'code': 'hacker',
    }, format='json')
    assert resp.status_code == 403


# ── RETRIEVE ─────────────────────────────────────────────

@pytest.mark.django_db
def test_get_role_detail(authed_client, root_role):
    """GET /api/rbac/roles/{id}/ → 200。"""
    client, _ = authed_client
    resp = client.get(f'/api/rbac/roles/{root_role.id}/')
    assert resp.status_code == 200
    assert resp.data['data']['code'] == 'root'


@pytest.mark.django_db
def test_get_role_not_found(authed_client):
    """不存在的角色 → 404。"""
    client, _ = authed_client
    resp = client.get('/api/rbac/roles/99999/')
    assert resp.status_code == 404


# ── UPDATE ───────────────────────────────────────────────

@pytest.mark.django_db
def test_update_role(authed_client, root_role):
    """PUT 更新角色 → 200。"""
    client, _ = authed_client
    resp = client.put(f'/api/rbac/roles/{root_role.id}/', {
        'description': '系统超级管理员',
    }, format='json')
    assert resp.status_code == 200
    root_role.refresh_from_db()
    assert root_role.description == '系统超级管理员'


@pytest.mark.django_db
def test_update_system_role_code_protected(authed_client, root_role):
    """系统角色编码不可修改 → 403。"""
    client, _ = authed_client
    resp = client.put(f'/api/rbac/roles/{root_role.id}/', {
        'code': 'not_root',
    }, format='json')
    assert resp.status_code == 403
    assert resp.data['error']['code'] == 'SYSTEM_ROLE_PROTECTED'


# ── DELETE ───────────────────────────────────────────────

@pytest.mark.django_db
def test_delete_system_role_protected(authed_client, root_role):
    """删除 root 系统角色 → 403。"""
    client, _ = authed_client
    resp = client.delete(f'/api/rbac/roles/{root_role.id}/')
    assert resp.status_code == 403
    assert resp.data['error']['code'] == 'SYSTEM_ROLE_PROTECTED'


@pytest.mark.django_db
def test_delete_boss_role_protected(authed_client, boss_role):
    """删除 boss 系统角色 → 403。"""
    client, _ = authed_client
    resp = client.delete(f'/api/rbac/roles/{boss_role.id}/')
    assert resp.status_code == 403


@pytest.mark.django_db
def test_delete_user_role_protected(authed_client, user_role):
    """删除 user 系统角色 → 403。"""
    client, _ = authed_client
    resp = client.delete(f'/api/rbac/roles/{user_role.id}/')
    assert resp.status_code == 403


@pytest.mark.django_db
def test_delete_normal_role(authed_client):
    """删除普通角色 → 204。"""
    client, _ = authed_client
    role = Role.objects.create(name='临时角色', code='temp')
    resp = client.delete(f'/api/rbac/roles/{role.id}/')
    assert resp.status_code == 204


@pytest.mark.django_db
def test_delete_normal_role_clears_user_roles(authed_client, normal_user):
    """删除角色后解除用户关联。"""
    client, _ = authed_client
    role = Role.objects.create(name='临时角色', code='temp')
    UserRole.objects.create(user=normal_user, role=role)
    assert UserRole.objects.filter(role=role).count() == 1

    client.delete(f'/api/rbac/roles/{role.id}/')
    assert UserRole.objects.filter(role=role).count() == 0
