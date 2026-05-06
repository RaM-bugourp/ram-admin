"""
RBAC 权限测试
"""

import pytest
from apps.rbac.models import Menu, Role, Permission


class TestMenu:
    """菜单测试"""

    def test_list_menus(self, authenticated_client):
        """测试获取菜单列表"""
        response = authenticated_client.get('/api/rbac/menus/')
        assert response.status_code == 200

    def test_create_menu(self, authenticated_client):
        """测试创建菜单"""
        response = authenticated_client.post('/api/rbac/menus/', {
            'title': '测试菜单',
            'path': '/test',
            'component': 'test/index',
            'icon': 'icon-test',
        })
        assert response.status_code == 201

    def test_get_menu_tree(self, authenticated_client):
        """测试获取菜单树"""
        response = authenticated_client.get('/api/rbac/menus/tree/')
        assert response.status_code == 200
        assert isinstance(response.data, list)


class TestRole:
    """角色测试"""

    def test_list_roles(self, authenticated_client):
        """测试获取角色列表"""
        response = authenticated_client.get('/api/rbac/roles/')
        assert response.status_code == 200

    def test_create_role(self, authenticated_client):
        """测试创建角色"""
        response = authenticated_client.post('/api/rbac/roles/', {
            'name': '测试角色',
            'code': 'test_role',
            'description': '测试用角色',
        })
        assert response.status_code == 201


class TestPermission:
    """权限测试"""

    def test_list_permissions(self, authenticated_client):
        """测试获取权限列表"""
        response = authenticated_client.get('/api/rbac/permissions/')
        assert response.status_code == 200
