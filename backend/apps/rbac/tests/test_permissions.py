"""Tests for permission enforcement — IsAdminOrReadOnly."""
import pytest
from apps.rbac.models import Role
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_admin_can_write_users(authed_client):
    """root 用户可以创建用户。"""
    client, _ = authed_client
    resp = client.post('/api/rbac/users/', {
        'username': 'newbie', 'email': 'n@t.com', 'password': 'pass123',
    }, format='json')
    assert resp.status_code == 201


@pytest.mark.django_db
def test_boss_can_write_users(boss_client):
    """BOSS 用户可以创建用户。"""
    client, _ = boss_client
    resp = client.post('/api/rbac/users/', {
        'username': 'boss_create', 'email': 'bc@t.com', 'password': 'pass123',
    }, format='json')
    assert resp.status_code == 201


@pytest.mark.django_db
def test_normal_user_readonly(normal_client):
    """普通用户只能读，不能写。"""
    client, _ = normal_client
    # GET → 200
    resp = client.get('/api/rbac/users/')
    assert resp.status_code == 200

    # POST → 403
    resp = client.post('/api/rbac/users/', {
        'username': 'hacker', 'email': 'h@t.com', 'password': 'pass123',
    }, format='json')
    assert resp.status_code == 403


@pytest.mark.django_db
def test_unauthenticated_user_denied(api_client):
    """未登录用户 → 403（IsAuthenticated 优先）。"""
    # GET → 403（未登录）
    resp = api_client.get('/api/rbac/users/')
    assert resp.status_code == 403


@pytest.mark.django_db
def test_normal_user_readonly_role(normal_client):
    """普通用户角色只读。"""
    client, _ = normal_client
    # GET → 200
    resp = client.get('/api/rbac/roles/')
    assert resp.status_code == 200

    # POST → 403
    resp = client.post('/api/rbac/roles/', {
        'name': 'hack_role', 'code': 'hack',
    }, format='json')
    assert resp.status_code == 403

    # DELETE → 403
    resp = client.delete('/api/rbac/roles/1/')
    assert resp.status_code == 403
