"""Tests for RoleService — unit tests, not through HTTP."""
import pytest
from apps.rbac.services.role_service import RoleService
from apps.rbac.models import Role, UserRole
from apps.common.exceptions import BusinessError

svc = RoleService()


# ── CREATE ───────────────────────────────────────────────

@pytest.mark.django_db
def test_create_role():
    """create_role 返回 Role 实例。"""
    role = svc.create_role({'name': '测试角色', 'code': 'test', 'description': 'desc'})
    assert role.name == '测试角色'
    assert role.code == 'test'
    assert Role.objects.filter(code='test').exists()


@pytest.mark.django_db
def test_create_role_duplicate_name(root_role):
    """重复角色名抛出 BusinessError。"""
    with pytest.raises(BusinessError) as exc:
        svc.create_role({'name': '管理员', 'code': 'admin2'})
    assert exc.value.code == 'DUPLICATE_ROLE_NAME'


@pytest.mark.django_db
def test_create_role_duplicate_code(root_role):
    """重复编码抛出 BusinessError。"""
    with pytest.raises(BusinessError) as exc:
        svc.create_role({'name': '复制管理员', 'code': 'root'})
    assert exc.value.code == 'DUPLICATE_ROLE_CODE'


# ── LIST ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_list_roles(root_role, user_role):
    """list_roles 返回所有角色。"""
    roles = svc.list_roles()
    codes = [r.code for r in roles]
    assert 'root' in codes
    assert 'user' in codes


# ── GET DETAIL ───────────────────────────────────────────

@pytest.mark.django_db
def test_get_role_detail(root_role):
    """get_role_detail 返回角色。"""
    role = svc.get_role_detail(root_role.id)
    assert role is not None
    assert role.code == 'root'


@pytest.mark.django_db
def test_get_role_detail_not_found():
    """不存在的角色返回 None。"""
    assert svc.get_role_detail(99999) is None


# ── UPDATE ───────────────────────────────────────────────

@pytest.mark.django_db
def test_update_role(root_role):
    """update_role 更新字段。"""
    updated = svc.update_role(root_role.id, {'description': '新描述'})
    assert updated.description == '新描述'


@pytest.mark.django_db
def test_update_role_not_found():
    """不存在的角色抛出 BusinessError。"""
    with pytest.raises(BusinessError) as exc:
        svc.update_role(99999, {'description': 'x'})
    assert exc.value.code == 'ROLE_NOT_FOUND'


@pytest.mark.django_db
def test_update_system_role_code_protected(root_role):
    """系统角色编码不可修改。"""
    with pytest.raises(BusinessError) as exc:
        svc.update_role(root_role.id, {'code': 'not_root'})
    assert exc.value.code == 'SYSTEM_ROLE_PROTECTED'


# ── DELETE ───────────────────────────────────────────────

@pytest.mark.django_db
def test_delete_system_role_protected(root_role):
    """系统角色不可删除。"""
    with pytest.raises(BusinessError) as exc:
        svc.delete_role(root_role.id)
    assert exc.value.code == 'SYSTEM_ROLE_PROTECTED'


@pytest.mark.django_db
def test_delete_normal_role():
    """普通角色可删除（软删除）。"""
    role = Role.objects.create(name='temp', code='temp')
    svc.delete_role(role.id)
    role.refresh_from_db()
    assert role.is_deleted is True


@pytest.mark.django_db
def test_delete_role_not_found():
    """不存在的角色抛出 BusinessError。"""
    with pytest.raises(BusinessError) as exc:
        svc.delete_role(99999)
    assert exc.value.code == 'ROLE_NOT_FOUND'


# ── BOSS UNIQUE ──────────────────────────────────────────

@pytest.mark.django_db
def test_enforce_unique_role_boss(boss_user, boss_role):
    """BOSS 唯一性校验：第二个 BOSS 应失败。"""
    with pytest.raises(BusinessError) as exc:
        RoleService.enforce_unique_role(99999, [boss_role.id])
    assert exc.value.code == 'UNIQUE_ROLE_CONFLICT'


@pytest.mark.django_db
def test_enforce_unique_role_same_user_ok(boss_user, boss_role):
    """同一用户再次分配 BOSS 角色应通过（更新场景）。"""
    # 没有异常=通过
    RoleService.enforce_unique_role(boss_user.id, [boss_role.id])


@pytest.mark.django_db
def test_enforce_unique_role_non_unique_ok(normal_user, user_role):
    """非唯一角色不受限制。"""
    RoleService.enforce_unique_role(normal_user.id, [user_role.id])
