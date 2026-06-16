"""Tests for BaseManager — soft-delete filtering logic.
Uses actual project models (Role) which inherit from BaseModel via BaseManager.
"""
import pytest
from apps.rbac.models import Role


@pytest.mark.django_db
def test_manager_filters_deleted():
    """get_queryset() 默认过滤 is_deleted=True。"""
    obj1 = Role.objects.create(name='visible', code='vis')
    obj2 = Role.objects.create(name='hidden', code='hid')
    obj2.soft_delete()

    qs = list(Role.objects.all())
    assert obj1 in qs
    assert obj2 not in qs


@pytest.mark.django_db
def test_manager_with_deleted():
    """with_deleted() 返回全部记录。"""
    obj = Role.objects.create(name='test_role', code='test_code')
    obj.soft_delete()

    qs = Role.objects.with_deleted()
    assert obj in qs
    assert qs.count() == 1


@pytest.mark.django_db
def test_manager_create_returns_visible():
    """新创建的对象默认可见（is_deleted=False）。"""
    obj = Role.objects.create(name='fresh', code='fr')
    obj.refresh_from_db()
    assert obj.is_deleted is False
    assert Role.objects.filter(id=obj.id).exists()


@pytest.mark.django_db
def test_manager_multiple_deleted():
    """多个软删除对象被正确过滤。"""
    roles = []
    for i in range(5):
        r = Role.objects.create(name=f'test_{i}', code=f'c{i}')
        if i % 2 == 0:
            r.soft_delete()
        roles.append(r)

    visible = list(Role.objects.all())
    # indices 1, 3 should remain
    assert len(visible) == 2


@pytest.mark.django_db
def test_manager_chain_with_deleted_and_filter():
    """with_deleted() 可以与 filter() 链式调用。"""
    obj = Role.objects.create(name='special', code='sp')
    obj.soft_delete()

    result = Role.objects.with_deleted().filter(name='special')
    assert result.count() == 1
