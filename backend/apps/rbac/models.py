"""
apps/rbac/models.py — RBAC 权限模型（ORM 层）
══════════════════════════════════════════════════════════════════

为什么放在 apps 里而不是 packages/core 里？
    packages/core/ —— 框架层，纯 Python，无 Django 依赖
    apps/rbac/     —— Django ORM 层，有 Django 模型定义

这样分层的好处：
    —— packages/core/ 可以被任何 Python 项目复用（不只是 Django）
    —— apps/rbac/ 只负责 Django 数据库模型的定义和业务关联
"""

from django.db import models
from django.apps import apps
from mptt.models import MPTTModel, TreeForeignKey

from apps.user.models import User  # noqa: F401


# ═══════════════════════════════════════════════════════════
# 1. Organization 组织模型（MPTT 树形结构）
# ═══════════════════════════════════════════════════════════

class Organization(MPTTModel):
    """
    组织模型 —— 支持无限层级树形结构。

    使用 MPTT（Modified Preorder Tree Traversal）实现。
    原理：在每个节点上存储 lft/rght（左右值），一次查询可拿到整棵树。
    优势：查询子树/祖先树不需要递归，O(1) 数据库查询。
    """

    name = models.CharField('组织名称', max_length=100)
    code = models.CharField('组织编码', max_length=50, unique=True, help_text='唯一标识，如 DEPT_IT')
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True, related_name='children',
        verbose_name='上级组织'
    )
    sort = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['sort']

    class Meta:
        db_table = 'sys_organization'
        verbose_name = '组织'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def get_ancestors(self, include_self=False):
        """获取所有祖先组织（包含自己）"""
        if include_self:
            return self.get_ancestors(include_self=False) | models.Q(pk=self.pk)
        return Organization.objects.filter(
            tree_id=self.tree_id, lft__lt=self.lft
        )

    def get_descendants(self, include_self=False):
        """获取所有后代组织"""
        return Organization.objects.filter(
            tree_id=self.tree_id,
            lft__gte=self.lft,
            rght__lte=self.rght,
        )


# ═══════════════════════════════════════════════════════════
# 2. Menu 菜单模型（动态菜单 + 前端路由）
# ═══════════════════════════════════════════════════════════

class Menu(models.Model):
    """
    动态菜单模型 —— 存储后端返回给前端的菜单树。

    前端菜单 = 后端菜单表 + 路由信息
    用户看到的侧边栏 = 当前角色关联的菜单

    设计要点：
        —— component 字段告诉前端用哪个 Vue 组件渲染
        —— path 字段是路由路径（用于 router.addRoute）
        —— parent_id 支持两种模式：自己管理 parent_id 或用 MPTT
    """

    title = models.CharField('菜单标题', max_length=50)
    name = models.CharField('路由名称', max_length=50, blank=True, default='')
    path = models.CharField('路由路径', max_length=200, blank=True, default='')
    icon = models.CharField('图标', max_length=50, blank=True, default='')
    component = models.CharField('组件路径', max_length=200, blank=True, default='',
                                  help_text='前端 src/views/ 下的路径，如 article/list')
    sort = models.IntegerField('排序', default=0)
    is_hidden = models.BooleanField('是否隐藏', default=False,
                                    help_text='隐藏菜单仍可访问，只是不显示在侧边栏')
    is_active = models.BooleanField('是否启用', default=True)

    # 角色关联通过 Role.menus M2M 实现（避免双向 M2M 冲突）

    # 树形支持（parent_id 自引用，非 MPTT，简单够用）
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True, related_name='children',
        verbose_name='上级菜单'
    )

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'sys_menu'
        verbose_name = '菜单'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return self.title

    def to_tree_node(self):
        """
        转换为前端菜单树节点。
        """
        node = {
            'id': self.id,
            'title': self.title,
            'name': self.name,
            'path': self.path,
            'icon': self.icon,
            'component': self.component,
            'isHidden': self.is_hidden,
            'sort': self.sort,
        }
        # 递归处理子菜单
        children = self.children.filter(is_active=True).order_by('sort', 'id')
        if children.exists():
            node['children'] = [child.to_tree_node() for child in children]
        return node


# ═══════════════════════════════════════════════════════════
# 3. Permission 权限模型
# ═══════════════════════════════════════════════════════════

class Permission(models.Model):
    """
    权限模型 —— 定义权限码（代码即权限）。

    权限码命名规范（与 Django 风格一致）：
        app:model:action
        如：user:user:list     （查看用户列表）
            article:article:create  （创建文章）

    两种授权方式：
        1. 菜单授权（Menu.roles 多对多）
        2. 角色权限授权（Role.permissions 多对多）
    """

    TYPE_CHOICES = [
        ('menu', '菜单权限'),
        ('button', '按钮权限'),
        ('field', '字段权限'),
        ('api', 'API权限'),
    ]

    name = models.CharField('权限名称', max_length=50)
    code = models.CharField(
        '权限码', max_length=100, unique=True,
        help_text='唯一标识，如 user:user:list，用于后端接口鉴权'
    )
    url_pattern = models.CharField(
        'URL匹配', max_length=200, blank=True, default='',
        help_text='URL 正则模式，如 ^/api/user/，用于 URL 模式鉴权'
    )
    menu = models.ForeignKey(
        Menu, on_delete=models.CASCADE,
        null=True, blank=True, related_name='permissions',
        verbose_name='关联菜单'
    )
    ptype = models.CharField('权限类型', max_length=20, choices=TYPE_CHOICES, default='api')
    is_active = models.BooleanField('是否启用', default=True)
    description = models.CharField('描述', max_length=255, blank=True, default='')
    sort = models.IntegerField('排序', default=0)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'sys_permission'
        verbose_name = '权限'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return f'{self.name}({self.code})'


# ═══════════════════════════════════════════════════════════
# 4. Role 角色模型
# ═══════════════════════════════════════════════════════════

class Role(models.Model):
    """
    角色模型 —— 关联用户、菜单、权限、数据范围。

    data_scope（数据范围）：
        ALL     — 全部数据（超管）
        org     — 本组织及下级
        SELF    — 仅本人数据
    """

    SCOPE_CHOICES = [
        ('ALL', '全部数据'),
        ('org', '本组织及下级'),
        ('dept', '本部门'),
        ('SELF', '仅本人数据'),
    ]

    name = models.CharField('角色名称', max_length=50)
    code = models.CharField('角色编码', max_length=50, unique=True,
                             help_text='唯一标识，如 role_admin')
    description = models.CharField('描述', max_length=255, blank=True, default='')
    data_scope = models.CharField('数据范围', max_length=20, choices=SCOPE_CHOICES, default='SELF')
    is_active = models.BooleanField('是否启用', default=True)
    sort = models.IntegerField('排序', default=0)

    # 多对多关联
    permissions = models.ManyToManyField(
        Permission, related_name='roles', blank=True,
        verbose_name='关联权限'
    )
    users = models.ManyToManyField(
        User, related_name='roles', blank=True,
        verbose_name='关联用户'
    )
    menus = models.ManyToManyField(
        Menu, related_name='roles', blank=True,
        verbose_name='关联菜单（用于侧边栏）'
    )

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'sys_role'
        verbose_name = '角色'
        verbose_name_plural = verbose_name
        ordering = ['sort', 'id']

    def __str__(self):
        return self.name

    def get_permission_codes(self):
        """获取角色所有权限码"""
        return list(self.permissions.values_list('code', flat=True))
