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
