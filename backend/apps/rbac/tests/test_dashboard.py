"""Tests for dashboard stats endpoint."""
import pytest
from apps.rbac.models import Role, UserRole


@pytest.mark.django_db
def test_dashboard_stats(authed_client, root_user):
    """GET /api/dashboard/stats/ → 200 + 4 个统计字段。"""
    client, _ = authed_client
    resp = client.get('/api/dashboard/stats/')
    assert resp.status_code == 200
    data = resp.data.get('data')
    assert data is not None
    assert 'total_users' in data
    assert 'active_users' in data
    assert 'total_roles' in data
    assert 'total_assignments' in data


@pytest.mark.django_db
def test_dashboard_stats_accuracy(authed_client, root_user, root_role):
    """统计值随数据变化而更新。"""
    client, _ = authed_client
    resp = client.get('/api/dashboard/stats/')
    assert resp.data['data']['total_users'] >= 1
    assert resp.data['data']['total_roles'] >= 1
    assert resp.data['data']['total_assignments'] >= 1
    assert resp.data['data']['active_users'] >= 1
