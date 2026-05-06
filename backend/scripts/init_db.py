#!/usr/bin/env python
"""
数据库初始化脚本
══════════════════════════════════════════════════════════════════

用法：
  python scripts/init_db.py

执行：
  1. 创建迁移文件
  2. 执行数据库迁移
  3. 创建初始数据（超管账户、示例菜单）
"""

import os
import sys

# 确保当前目录是 backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ram_admin.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.rbac.models import Menu, Role, Permission
from apps.article.models import Category

User = get_user_model()


def create_superuser():
    """创建超管账户"""
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@admin.com',
            password='admin123',
        )
        print('[OK] 管理员账号: admin / admin123')
    else:
        print('[SKIP] 管理员账号已存在')


def create_menus():
    """创建示例菜单"""
    if Menu.objects.exists():
        print('[SKIP] 菜单数据已存在')
        return

    # 顶级菜单
    system_menu = Menu.objects.create(
        title='系统管理', name='System', path='/system',
        icon='icon-setting', sort=1,
    )
    article_menu = Menu.objects.create(
        title='内容管理', name='Content', path='/article',
        icon='icon-book', sort=2,
    )

    # 子菜单
    Menu.objects.create(
        title='仪表盘', name='Dashboard', path='/dashboard',
        component='dashboard/index',
        parent=system_menu, sort=1,
    )
    Menu.objects.create(
        title='文章列表', name='ArticleList', path='/list',
        component='article/list',
        parent=article_menu, sort=1,
    )
    Menu.objects.create(
        title='分类管理', name='CategoryList', path='/category',
        component='article/category',
        parent=article_menu, sort=2,
    )

    print('[OK] 菜单数据创建完成')


def create_admin_role():
    """创建管理员角色"""
    if Role.objects.filter(code='admin').exists():
        print('[SKIP] 管理员角色已存在')
        return

    admin_role = Role.objects.create(
        name='超级管理员',
        code='admin',
        description='拥有所有权限',
        data_scope='ALL',
    )

    # 关联所有菜单
    admin_role.menus.set(Menu.objects.all())
    admin_role.save()

    # 关联 admin 用户
    admin = User.objects.get(username='admin')
    admin_role.users.add(admin)

    print('[OK] 管理员角色创建完成')


def main():
    print('=' * 50)
    print('RaM Admin 数据库初始化')
    print('=' * 50)

    from django.core.management import call_command
    print('\n[1/3] 生成迁移文件...')
    call_command('makemigrations', '--noinput')

    print('\n[2/3] 执行数据库迁移...')
    call_command('migrate', '--noinput')

    print('\n[3/3] 创建初始数据...')
    create_superuser()
    create_menus()
    create_admin_role()

    print('\n' + '=' * 50)
    print('初始化完成！')
    print('启动后端: python manage.py runserver')
    print('启动前端: cd ../frontend && npm run dev')
    print('=' * 50)


if __name__ == '__main__':
    main()
