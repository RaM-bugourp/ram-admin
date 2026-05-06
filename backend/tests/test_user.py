"""
用户认证测试
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


class TestUserLogin:
    """登录测试"""

    def test_login_success(self, api_client, admin_user):
        """测试登录成功"""
        response = api_client.post('/api/auth/login/', {
            'username': 'admin',
            'password': 'admin123',
        })
        assert response.status_code == 200

    def test_login_wrong_password(self, api_client, admin_user):
        """测试密码错误"""
        response = api_client.post('/api/auth/login/', {
            'username': 'admin',
            'password': 'wrong_password',
        })
        assert response.status_code == 401

    def test_login_user_not_exist(self, api_client):
        """测试用户不存在"""
        response = api_client.post('/api/auth/login/', {
            'username': 'not_exist',
            'password': 'password',
        })
        assert response.status_code == 401


class TestUserInfo:
    """用户信息测试"""

    def test_get_user_info_unauthenticated(self, api_client):
        """测试未登录获取用户信息"""
        response = api_client.get('/api/auth/user_info/')
        assert response.status_code == 401

    def test_get_user_info_authenticated(self, authenticated_client, admin_user):
        """测试已登录获取用户信息"""
        response = authenticated_client.get('/api/auth/user_info/')
        assert response.status_code == 200
        assert response.data['username'] == 'admin'


class TestUserLogout:
    """登出测试"""

    def test_logout(self, authenticated_client):
        """测试登出"""
        response = authenticated_client.post('/api/auth/logout/')
        assert response.status_code == 200
