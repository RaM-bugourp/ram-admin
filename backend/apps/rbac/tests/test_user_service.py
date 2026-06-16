"""Tests for UserService — unit tests, not through HTTP."""
import pytest
from apps.rbac.services.user_service import UserService
from apps.rbac.models import User
from apps.common.exceptions import BusinessError

svc = UserService()


@pytest.mark.django_db
def test_list_users_pagination(root_user, normal_user):
    """list_users 返回正确分页结构。"""
    result = svc.list_users(page=1, page_size=10)
    assert 'items' in result
    assert 'page' in result
    assert 'total' in result
    assert result['page'] == 1
    assert result['total'] >= 2


@pytest.mark.django_db
def test_list_users_search(root_user):
    """search 参数正确过滤。"""
    result = svc.list_users(search='admin')
    assert result['total'] >= 1
    assert any(u.username == 'admin' for u in result['items'])


@pytest.mark.django_db
def test_list_users_search_no_match(root_user):
    """无匹配 search 返回空。"""
    result = svc.list_users(search='zzz_no_match_zzz')
    assert result['total'] == 0


@pytest.mark.django_db
def test_get_user_detail(root_user):
    """get_user_detail 返回用户。"""
    user = svc.get_user_detail(root_user.id)
    assert user is not None
    assert user.id == root_user.id


@pytest.mark.django_db
def test_get_user_detail_not_found():
    """不存在的用户返回 None。"""
    user = svc.get_user_detail(99999)
    assert user is None


@pytest.mark.django_db
def test_create_user_success():
    """create_user 返回 User 实例。"""
    user = svc.create_user({
        'username': 'svc_user',
        'email': 'svc@test.com',
        'password': 'pass123',
    })
    assert user is not None
    assert user.username == 'svc_user'
    assert User.objects.filter(username='svc_user').exists()


@pytest.mark.django_db
def test_create_user_duplicate_username(root_user):
    """重复用户名抛出 BusinessError。"""
    with pytest.raises(BusinessError) as exc:
        svc.create_user({
            'username': 'admin',
            'email': 'other@test.com',
            'password': 'pass123',
        })
    assert exc.value.code == 'DUPLICATE_USERNAME'


@pytest.mark.django_db
def test_create_user_duplicate_email(root_user):
    """重复邮箱抛出 BusinessError。"""
    with pytest.raises(BusinessError) as exc:
        svc.create_user({
            'username': 'other',
            'email': 'admin@test.com',
            'password': 'pass123',
        })
    assert exc.value.code == 'DUPLICATE_EMAIL'


@pytest.mark.django_db
def test_update_user(root_user):
    """update_user 更新字段。"""
    updated = svc.update_user(root_user.id, {'username': 'admin_v2'})
    assert updated.username == 'admin_v2'


@pytest.mark.django_db
def test_update_user_not_found():
    """不存在的用户抛出 BusinessError。"""
    with pytest.raises(BusinessError) as exc:
        svc.update_user(99999, {'username': 'ghost'})
    assert exc.value.code == 'USER_NOT_FOUND'


@pytest.mark.django_db
def test_delete_user_soft_delete(root_user):
    """delete_user 软删除用户。"""
    svc.delete_user(root_user.id)
    root_user.refresh_from_db()
    assert root_user.is_deleted is True


@pytest.mark.django_db
def test_delete_user_not_found():
    """删除不存在的用户抛出 BusinessError。"""
    with pytest.raises(BusinessError) as exc:
        svc.delete_user(99999)
    assert exc.value.code == 'USER_NOT_FOUND'


@pytest.mark.django_db
def test_reset_password(root_user):
    """reset_password 使新密码可用。"""
    svc.reset_password(root_user.id, 'new_secret')
    root_user.refresh_from_db()
    assert root_user.check_password('new_secret') is True
