"""Role management service — CRUD + unique-role enforcement."""
import logging
from django.db import transaction
from apps.common.exceptions import BusinessError
from apps.rbac.models import Role, UserRole

logger = logging.getLogger(__name__)


class RoleService:
    """角色业务逻辑."""

    # ── 查询 ──────────────────────────────────────────────

    def list_roles(self) -> list[Role]:
        """获取所有有效角色列表（含用户数统计）."""
        roles = list(Role.objects.order_by('id'))
        for role in roles:
            role.user_count = UserRole.objects.filter(role=role).count()
        return roles

    def get_role_detail(self, role_id: int) -> Role | None:
        """获取单个角色详情."""
        return Role.objects.filter(id=role_id).first()

    # ── 写操作 ────────────────────────────────────────────

    @transaction.atomic
    def create_role(self, data: dict) -> Role:
        """创建角色."""
        name = data['name']
        code = data['code']
        is_unique = data.get('is_unique', False)

        if Role.objects.filter(name=name).exists():
            raise BusinessError(
                message=f'角色名 "{name}" 已存在', code='DUPLICATE_ROLE_NAME', status=409
            )
        if Role.objects.filter(code=code).exists():
            raise BusinessError(
                message=f'角色编码 "{code}" 已存在', code='DUPLICATE_ROLE_CODE', status=409
            )

        role = Role.objects.create(
            name=name,
            code=code,
            description=data.get('description', ''),
            is_unique=is_unique,
        )
        logger.info('Role created', extra={'role_id': role.id, 'code': code})
        return role

    @transaction.atomic
    def update_role(self, role_id: int, data: dict) -> Role:
        """更新角色."""
        role = Role.objects.filter(id=role_id).first()
        if not role:
            raise BusinessError(message='角色不存在', code='ROLE_NOT_FOUND', status=404)

        # 保护系统角色: root / user / boss 不可改名
        if role.code in ('root', 'user', 'boss') and 'code' in data and data['code'] != role.code:
            raise BusinessError(
                message=f'系统角色 "{role.name}" 编码不可修改',
                code='SYSTEM_ROLE_PROTECTED', status=403
            )

        if 'name' in data and data['name'] != role.name:
            if Role.objects.filter(name=data['name']).exists():
                raise BusinessError(message='角色名已存在', code='DUPLICATE_ROLE_NAME', status=409)
            role.name = data['name']

        if 'code' in data and data['code'] != role.code:
            if Role.objects.filter(code=data['code']).exists():
                raise BusinessError(message='角色编码已存在', code='DUPLICATE_ROLE_CODE', status=409)
            role.code = data['code']

        if 'description' in data:
            role.description = data['description']
        if 'is_unique' in data:
            role.is_unique = data['is_unique']

        role.save()
        logger.info('Role updated', extra={'role_id': role_id})
        return role

    def delete_role(self, role_id: int) -> None:
        """删除角色 — 系统角色不可删除."""
        role = Role.objects.filter(id=role_id).first()
        if not role:
            raise BusinessError(message='角色不存在', code='ROLE_NOT_FOUND', status=404)

        if role.code in ('root', 'user', 'boss'):
            raise BusinessError(
                message=f'系统角色 "{role.name}" 不可删除',
                code='SYSTEM_ROLE_PROTECTED', status=403
            )

        # 解除所有持有该角色的用户关联
        UserRole.objects.filter(role=role).delete()
        role.soft_delete()
        logger.info('Role deleted', extra={'role_id': role_id, 'code': role.code})

    # ── BOSS 唯一性 ──────────────────────────────────────

    @staticmethod
    def enforce_unique_role(user_id: int, role_ids: list[int]) -> None:
        """
        检查并强制执行唯一角色约束.

        规则: 如果 role_ids 中包含某个 is_unique=True 的角色，
        确保全局没有其他用户持有该角色。

        当前场景: code='boss' 的角色 is_unique=True，全局只能有一个 BOSS。
        """
        unique_roles = Role.objects.filter(id__in=role_ids, is_unique=True)
        if not unique_roles.exists():
            return

        for unique_role in unique_roles:
            existing = UserRole.objects.filter(
                role=unique_role
            ).exclude(user_id=user_id).first()
            if existing:
                from apps.rbac.models import User
                current_holder = User.objects.filter(id=existing.user_id).first()
                holder_name = current_holder.username if current_holder else '未知'
                raise BusinessError(
                    message=f'角色 "{unique_role.name}" 是唯一角色，当前由用户 "{holder_name}" 持有',
                    code='UNIQUE_ROLE_CONFLICT', status=409
                )
