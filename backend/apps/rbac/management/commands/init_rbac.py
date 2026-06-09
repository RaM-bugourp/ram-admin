"""Management command — create default roles and superuser."""
from django.core.management.base import BaseCommand
from apps.rbac.models import User, Role


class Command(BaseCommand):
    help = 'Initialize RBAC data: create roles (root/user/boss) and a root superuser'

    def handle(self, *args, **options):
        # 1. 创建系统角色
        default_roles = [
            {'name': '超级管理员', 'code': 'root', 'description': '系统最高权限，不受权限控制', 'is_unique': False},
            {'name': '普通用户', 'code': 'user', 'description': '基础访问权限', 'is_unique': False},
            {'name': 'BOSS', 'code': 'boss', 'description': '唯一最高决策账号', 'is_unique': True},
        ]

        for role_data in default_roles:
            role, created = Role.objects.get_or_create(
                code=role_data['code'],
                defaults=role_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Role "{role.name}" created (code={role.code}, is_unique={role.is_unique}).'))
            else:
                self.stdout.write(self.style.WARNING(f'Role "{role.name}" already exists, skipping.'))

        # 2. 创建 root 超级管理员
        username = 'admin'
        email = 'admin@adminx.local'
        password = 'admin123'

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists, skipping.'))
            return

        user = User.objects.create_superuser(username=username, email=email, password=password)

        # 给 admin 分配 root 角色
        root_role = Role.objects.by_code('root').first()
        if root_role:
            from apps.rbac.models import UserRole
            UserRole.objects.create(user=user, role=root_role)

        self.stdout.write(self.style.SUCCESS(f'Root superuser "{username}" created.'))
        self.stdout.write(f'  Username: {username}')
        self.stdout.write(f'  Password: {password}')
        self.stdout.write(f'  Role: root (超级管理员)')
        self.stdout.write(f'  BOSS role is available but not assigned to any user.')
