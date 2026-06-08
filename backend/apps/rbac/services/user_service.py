"""User management service — CRUD, pagination, search."""
import logging
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from apps.common.exceptions import BusinessError
from apps.rbac.models import User, UserRole

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class UserService:
    """用户业务逻辑."""

    # ── 查询 ────────────────────────────────────────────────

    def list_users(self, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE,
                   search: str = '') -> dict:
        """
        GET 分页列表，支持 username / email 模糊搜索.

        Returns:
            {items: [...], page: int, page_size: int, total: int}
        """
        page_size = min(page_size, MAX_PAGE_SIZE)
        qs = User.objects.order_by('-created_at')

        if search:
            qs = qs.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search)
            )

        paginator = Paginator(qs, page_size)
        page_obj = paginator.get_page(page)

        return {
            'items': list(page_obj.object_list),
            'page': page_obj.number,
            'page_size': page_size,
            'total': paginator.count,
            'total_pages': paginator.num_pages,
        }

    def get_user_detail(self, user_id: int) -> User | None:
        """获取单个用户详情（含角色信息）."""
        return User.objects.filter(id=user_id).first()

    # ── 写操作 ──────────────────────────────────────────────

    @transaction.atomic
    def create_user(self, data: dict) -> User:
        """
        创建用户 + 分配角色.

        Args:
            data: {username, email, password, is_active?, role_ids?}

        Raises:
            BusinessError: 用户名/邮箱重复
        """
        username = data['username']
        email = data['email']

        if User.objects.filter(username=username).exists():
            raise BusinessError(message=f'用户名 "{username}" 已存在', code='DUPLICATE_USERNAME', status=409)
        if User.objects.filter(email=email).exists():
            raise BusinessError(message=f'邮箱 "{email}" 已存在', code='DUPLICATE_EMAIL', status=409)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=data['password'],
            is_active=data.get('is_active', True),
        )

        # 分配角色
        role_ids = data.get('role_ids', [])
        if role_ids:
            user_roles = [UserRole(user=user, role_id=rid) for rid in role_ids]
            UserRole.objects.bulk_create(user_roles)

        logger.info('User created', extra={'user_id': user.id, 'username': username})
        return user

    @transaction.atomic
    def update_user(self, user_id: int, data: dict) -> User:
        """
        更新用户信息.

        Args:
            data: {username?, email?, is_active?, role_ids?}
        """
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise BusinessError(message='用户不存在', code='USER_NOT_FOUND', status=404)

        # 用户名去重检查
        if 'username' in data and data['username'] != user.username:
            if User.objects.filter(username=data['username']).exists():
                raise BusinessError(message='用户名已存在', code='DUPLICATE_USERNAME', status=409)
            user.username = data['username']

        # 邮箱去重检查
        if 'email' in data and data['email'] != user.email:
            if User.objects.filter(email=data['email']).exists():
                raise BusinessError(message='邮箱已存在', code='DUPLICATE_EMAIL', status=409)
            user.email = data['email']

        if 'is_active' in data:
            user.is_active = data['is_active']

        user.save()

        # 全量替换角色
        if 'role_ids' in data:
            UserRole.objects.filter(user=user).delete()
            if data['role_ids']:
                user_roles = [UserRole(user=user, role_id=rid) for rid in data['role_ids']]
                UserRole.objects.bulk_create(user_roles)

        logger.info('User updated', extra={'user_id': user_id})
        return user

    def delete_user(self, user_id: int) -> None:
        """软删除用户."""
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise BusinessError(message='用户不存在', code='USER_NOT_FOUND', status=404)
        user.soft_delete()
        logger.info('User soft-deleted', extra={'user_id': user_id})

    def reset_password(self, user_id: int, new_password: str) -> None:
        """重置密码."""
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise BusinessError(message='用户不存在', code='USER_NOT_FOUND', status=404)
        user.set_password(new_password)
        user.save(update_fields=['password_hash'])
        logger.info('Password reset', extra={'user_id': user_id})
