"""RBAC models — User, Role, Permission, Menu."""
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from apps.common.base_model import BaseModel
from apps.common.managers import BaseManager


class UserManager(BaseManager):
    """Custom manager for the User model."""

    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('username is required')
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

    def active(self):
        return self.filter(is_active=True)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User — replaces Django's default User."""

    username = models.CharField(max_length=150, unique=True, verbose_name="用户名")
    email = models.EmailField(unique=True, verbose_name="邮箱")
    password_hash = models.CharField(max_length=255, verbose_name="密码哈希")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    last_login_at = models.DateTimeField(null=True, blank=True, verbose_name="最后登录")
    is_superuser = models.BooleanField(default=False, verbose_name="超级用户")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_deleted = models.BooleanField(default=False, verbose_name="软删除")

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'rbac_users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        indexes = [
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(fields=['username'], name='idx_user_username'),
        ]

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, value):
        self.set_password(value)

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return self.username

    def soft_delete(self):
        """软删除用户."""
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])


class RoleManager(BaseManager):
    """Role query helpers."""

    def by_code(self, code: str):
        return self.filter(code=code)


class Role(BaseModel):
    """角色 — 权限的集合."""

    name = models.CharField(max_length=100, unique=True, verbose_name="角色名")
    code = models.CharField(max_length=50, unique=True, verbose_name="角色编码")
    description = models.TextField(default="", blank=True, verbose_name="描述")
    is_unique = models.BooleanField(
        default=False,
        verbose_name="唯一角色",
        help_text="开启后全局只能有一个用户持有该角色（如 BOSS）"
    )

    objects = RoleManager()

    class Meta:
        db_table = 'rbac_roles'
        verbose_name = '角色'
        verbose_name_plural = '角色'

    def __str__(self):
        return self.name


class UserRole(BaseModel):
    """用户-角色关联（中间表）."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True, verbose_name="用户")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_index=True, verbose_name="角色")

    objects = BaseManager()

    class Meta:
        db_table = 'rbac_user_roles'
        verbose_name = '用户角色'
        verbose_name_plural = '用户角色'
        unique_together = [['user', 'role']]

    def __str__(self):
        return f"{self.user_id} → {self.role_id}"


class RolePermission(BaseModel):
    """角色-权限关联（预留扩展）."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_index=True, verbose_name="角色")
    permission_code = models.CharField(max_length=100, verbose_name="权限编码")

    objects = BaseManager()

    class Meta:
        db_table = 'rbac_role_permissions'
        verbose_name = '角色权限'
        verbose_name_plural = '角色权限'
        unique_together = [['role', 'permission_code']]

    def __str__(self):
        return f"{self.role.code}:{self.permission_code}"
