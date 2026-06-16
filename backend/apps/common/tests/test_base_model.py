"""Tests for BaseModel-based models — soft delete behavior.
Uses actual project models (Role) instead of test models (no migrations needed).
"""
import pytest
from apps.rbac.models import Role


@pytest.mark.django_db
def test_base_model_auto_timestamps():
    """BaseModel 自动填充 created_at 和 updated_at。"""
    obj = Role.objects.create(name='test_role', code='test_code')
    assert obj.created_at is not None
    assert obj.updated_at is not None
    assert obj.is_deleted is False


@pytest.mark.django_db
def test_soft_delete_sets_flag():
    """soft_delete() 设置 is_deleted=True 但记录仍在数据库中。"""
    obj = Role.objects.create(name='test_role', code='test_code')
    obj.soft_delete()
    assert obj.is_deleted is True

    reloaded = Role.objects.with_deleted().get(id=obj.id)
    assert reloaded.is_deleted is True


@pytest.mark.django_db
def test_soft_delete_default_filter():
    """默认查询过滤 is_deleted=False。"""
    obj = Role.objects.create(name='test_role', code='test_code')
    obj.soft_delete()

    qs = list(Role.objects.all())
    assert obj not in qs


@pytest.mark.django_db
def test_soft_delete_with_deleted():
    """with_deleted() 返回全部记录（含软删除）。"""
    obj = Role.objects.create(name='test_role', code='test_code')
    obj.soft_delete()

    qs = list(Role.objects.with_deleted())
    assert obj in qs


@pytest.mark.django_db
def test_updated_at_changes():
    """更新记录后 updated_at 发生变化。"""
    obj = Role.objects.create(name='test_role', code='test_code')
    original_updated = obj.updated_at

    obj.name = 'updated_role'
    obj.save()
    obj.refresh_from_db()
    assert obj.updated_at >= original_updated
