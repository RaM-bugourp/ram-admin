"""
RaM Admin 初始化数据脚本
════════════════════════════════════════════════════════════════

运行方式（在 backend/ 目录下，venv 激活后）：
    py scripts/init_data.py

功能：
  1. 创建超级管理员角色（role_admin）
  2. 创建完整菜单树
  3. 创建权限码
  4. 创建默认组织
  5. 确保 admin 用户存在并关联超级管理员角色
"""

import os
import sys

# ─────────────────────────────────────────────────────────────────
# 0. Django 环境初始化（必须在最前面）
# ─────────────────────────────────────────────────────────────────

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ram_admin.settings')
_project_root = os.path.dirname(os.path.abspath(__file__)) + '/..'
sys.path.insert(0, os.path.abspath(_project_root))
sys.path.insert(0, os.path.abspath(_project_root + '/../packages'))

import django
django.setup()

from django.contrib.auth import get_user_model
from apps.rbac.models import Menu, Organization, Permission, Role
from apps.user.models import User

User = get_user_model()

# ═══════════════════════════════════════════════════════════
# 1. 创建默认组织
# ═══════════════════════════════════════════════════════════

print('[1/5] 创建默认组织...')
org, _ = Organization.objects.get_or_create(
    code='ROOT',
    defaults={
        'name': '总部',
        'sort': 0,
        'is_active': True,
    }
)
print(f'  ✓ 组织：{org.name} (id={org.id})')

# ═══════════════════════════════════════════════════════════
# 2. 创建菜单树
# ═══════════════════════════════════════════════════════════

print('[2/5] 创建菜单树...')

# 先清空现有菜单（方便重复运行）
Menu.objects.all().delete()

menus = {}

def add_menu(title, path, component='', icon='', parent=None, name='', sort=0):
    """辅助函数：创建菜单节点"""
    m = Menu.objects.create(
        title=title,
        name=name or path.strip('/').replace('/', '_') or 'home',
        path=path,
        component=component,
        icon=icon,
        parent=parent,
        sort=sort,
        is_active=True,
    )
    menus[title] = m
    print(f'  ✓ 菜单：{title} ({path})')
    return m


# 一级菜单（无 parent）
dashboard = add_menu('首页', '/', component='dashboard/index', icon='icon-dashboard', sort=0, name='home')

sys_menu = add_menu('系统管理', '/system', icon='icon-settings', sort=100)
article_menu = add_menu('内容管理', '/article', icon='icon-edit', sort=200)

# 系统管理子菜单
user_menu = add_menu('用户管理', '/system/user', component='system/user/index', icon='icon-user', parent=sys_menu, sort=10)
role_menu = add_menu('角色管理', '/system/role', component='system/role/index', icon='icon-safe', parent=sys_menu, sort=20)
menu_menu = add_menu('菜单管理', '/system/menu', component='system/menu/index', icon='icon-nav', parent=sys_menu, sort=30)
org_menu = add_menu('组织管理', '/system/org', component='system/org/index', icon='icon-buiding', parent=sys_menu, sort=40)
audit_menu = add_menu('操作日志', '/system/audit', component='system/audit/index', icon='icon-history', parent=sys_menu, sort=50)

# 内容管理子菜单
article_list = add_menu('文章列表', '/article/list', component='article/list', icon='icon-list', parent=article_menu, sort=10)
article_category = add_menu('文章分类', '/article/category', component='article/category/index', icon='icon-tag', parent=article_menu, sort=20)

print(f'  共创建 {Menu.objects.count()} 个菜单节点')

# ═══════════════════════════════════════════════════════════
# 3. 创建权限码
# ═══════════════════════════════════════════════════════════

print('[3/5] 创建权限码...')
Permission.objects.all().delete()

permissions_data = [
    # 用户管理
    ('用户列表', 'user:user:list', '', 'menu'),
    ('创建用户', 'user:user:create', '', 'button'),
    ('编辑用户', 'user:user:update', '', 'button'),
    ('删除用户', 'user:user:delete', '', 'button'),
    # 角色管理
    ('角色列表', 'rbac:role:list', '', 'menu'),
    ('创建角色', 'rbac:role:create', '', 'button'),
    ('编辑角色', 'rbac:role:update', '', 'button'),
    ('删除角色', 'rbac:role:delete', '', 'button'),
    # 菜单管理
    ('菜单列表', 'rbac:menu:list', '', 'menu'),
    ('创建菜单', 'rbac:menu:create', '', 'button'),
    ('编辑菜单', 'rbac:menu:update', '', 'button'),
    ('删除菜单', 'rbac:menu:delete', '', 'button'),
    # 组织管理
    ('组织列表', 'rbac:org:list', '', 'menu'),
    ('创建组织', 'rbac:org:create', '', 'button'),
    # 操作日志
    ('查看日志', 'audit:log:list', '', 'menu'),
    # 文章管理
    ('文章列表', 'article:article:list', '', 'menu'),
    ('创建文章', 'article:article:create', '', 'button'),
    ('编辑文章', 'article:article:update', '', 'button'),
    ('删除文章', 'article:article:delete', '', 'button'),
    ('文章分类', 'article:category:list', '', 'menu'),
]

perm_map = {}
for name, code, url_pattern, ptype in permissions_data:
    p = Permission.objects.create(
        name=name,
        code=code,
        url_pattern=url_pattern,
        ptype=ptype,
        is_active=True,
        sort=0,
    )
    perm_map[code] = p

print(f'  共创建 {Permission.objects.count()} 个权限码')

# ═══════════════════════════════════════════════════════════
# 4. 创建超级管理员角色
# ═══════════════════════════════════════════════════════════

print('[4/5] 创建超级管理员角色...')
role_admin, _ = Role.objects.get_or_create(
    code='role_admin',
    defaults={
        'name': '超级管理员',
        'description': '拥有所有权限，数据范围：全部',
        'data_scope': 'ALL',
        'is_active': True,
        'sort': 0,
    }
)

# 关联所有权限
all_perms = Permission.objects.all()
role_admin.permissions.set(all_perms)

# 关联所有菜单
all_menus = Menu.objects.filter(is_active=True)
role_admin.menus.set(all_menus)

print(f'  ✓ 角色：{role_admin.name} (权限数={all_perms.count()}, 菜单数={all_menus.count()})')

# ═══════════════════════════════════════════════════════════
# 5. 确保 admin 用户存在并关联角色
# ═══════════════════════════════════════════════════════════

print('[5/5] 创建/更新 admin 用户...')
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@example.com',
        'is_superuser': True,
        'is_staff': True,
        'is_active': True,
    }
)
if not created and not admin.is_superuser:
    admin.is_superuser = True
    admin.is_staff = True
    admin.is_active = True
    admin.save(update_fields=['is_superuser', 'is_staff', 'is_active'])

# 关联超级管理员角色
if not admin.roles.filter(pk=role_admin.pk).exists():
    admin.roles.add(role_admin)

# 设置密码（无论是否新建）
admin.set_password('admin123')
admin.save(update_fields=['password'])

print(f'  ✓ 用户：admin (创建={created}, is_superuser={admin.is_superuser})')

print()
print('=' * 50)
print('✅ 初始化完成！')
print('=' * 50)
print(f'  管理员账号：admin')
print(f'  管理员密码：admin123')
print(f'  菜单数量：  {Menu.objects.count()}')
print(f'  权限数量：  {Permission.objects.count()}')
print(f'  角色数量：  {Role.objects.count()}')
print(f'  用户数量：  {User.objects.count()}')
print('=' * 50)
