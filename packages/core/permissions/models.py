"""
RBAC 权限系统
══════════════════════════════════════════════════════════════════

本模块提供完整的 RBAC（Role-Based Access Control）权限控制能力：

    1. Permission 模型 —— 权限定义
    2. Role 模型 —— 角色（权限集合）
    3. RBACPermission —— API 级权限检查（DRF 权限类）
    4. rbac_permission —— 函数式权限装饰器（推荐用法）
    5. DataScopeFilter —— 数据范围过滤

══════════════════════════════════════════════════════════════════

RBAC 核心概念：

    User ←→ UserRole ←→ Role ←→ RolePermission ←→ Permission
              ↓
         Organization（组织用于数据隔离）

    Permission 包含两个维度：
        • code          —— 权限码，如 "article:list"、"article:create"
        • url_pattern   —— URL 模式，如 "/api/article/*"（用于 URL 匹配模式）

══════════════════════════════════════════════════════════════════

面试要点：

Q: 权限检查的执行时机？
A: 请求 → Authentication（认证，拿到 user） → Permission（权限检查）

Q: 为什么用 ManyToMany 而不是 ForeignKey？
A: 一个角色可以拥有多个权限，一个权限可以分配给多个角色

Q: 数据权限（DataScope）怎么实现？
A: 在 get_queryset() 中根据用户角色动态加 .filter(owner_organization__in=...)
"""

from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# ─────────────────────────────────────────────────────────────────
# 菜单（前端路由 + 按钮级别控制）
# ─────────────────────────────────────────────────────────────────

class Menu(models.Model):
    """
    动态菜单模型 —— 控制前端页面级访问权限。

    用户登录后，后端返回菜单树给前端，前端根据菜单渲染侧边栏。
    通过路由守卫（router.beforeEach）控制页面访问。

    注意：Menu 只是展示控制，不是安全边界。
    真正的安全控制靠 Permission（后端 API 权限）。
    """

    title = models.CharField(max_length=64, verbose_name='菜单名称')
    path = models.CharField(max_length=128, blank=True, default='', verbose_name='路由路径')
    component = models.CharField(max_length=128, blank=True, default='', verbose_name='组件路径')
    icon = models.CharField(max_length=64, blank=True, default='', verbose_name='图标')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.CASCADE, related_name='children', verbose_name='父级菜单'
    )
    is_hidden = models.BooleanField(default=False, verbose_name='是否隐藏')

    class Meta:
        verbose_name = '菜单'
        verbose_name_plural = '菜单'
        ordering = ['order', 'id']

    def __str__(self):
        return self.title

    def to_tree_node(self):
        """
        转换为前端菜单树节点。

        用于 /api/rbac/menu/tree/ 接口，返回给前端动态路由。
        """
        node = {
            'id': self.pk,
            'title': self.title,
            'path': self.path,
            'component': self.component,
            'icon': self.icon,
            'isHidden': self.is_hidden,
            'order': self.order,
        }
        children = list(self.children.filter(is_hidden=False).order_by('order'))
        if children:
            node['children'] = [child.to_tree_node() for child in children]
        return node


# ─────────────────────────────────────────────────────────────────
# 权限（API 端点级别）
# ─────────────────────────────────────────────────────────────────

class Permission(models.Model):
    """
    API 端点权限。

    每个 Permission 对应一个后端 API 接口。
    用户通过拥有 Role（角色）间接获得 Permission（权限）。

    两种定义方式（任选其一）：
        1. URL 匹配模式（向后兼容）
           —— 自动从 URL 路径推导权限，无需手动注册
           —— 缺点：改了 URL 就要同步改权限记录

        2. 权限码模式（推荐）
           —— 显式定义 code，如 "article:list"
           —— 用 @rbac_permission('article:list') 装饰器绑定
           —— 优点：代码即权限，git 可追踪
    """

    HTTP_METHOD_CHOICES = (
        ('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'),
        ('PATCH', 'PATCH'), ('DELETE', 'DELETE'), ('ANY', 'ANY'),
    )

    name = models.CharField(max_length=64, verbose_name='权限名称')
    code = models.CharField(max_length=64, blank=True, default='', verbose_name='权限编码', unique=True)
    http_method = models.CharField(max_length=6, choices=HTTP_METHOD_CHOICES, default='ANY', verbose_name='请求方法')
    url_pattern = models.CharField(max_length=256, blank=True, default='', verbose_name='URL 模式')
    menu = models.ForeignKey(
        Menu, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='permissions', verbose_name='所属菜单'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        verbose_name = '权限'
        verbose_name_plural = '权限'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['http_method']),
        ]

    def __str__(self):
        return f"{self.name}({self.code or self.url_pattern})"


# ─────────────────────────────────────────────────────────────────
# 角色
# ─────────────────────────────────────────────────────────────────

class Role(models.Model):
    """
    角色 —— 权限的集合。

    Role 是权限管理的核心单位：
        —— 不直接给用户分配 Permission（太零碎）
        —— 给用户分配 Role（Role 包含多个 Permission）
        —— 调整权限时只改 Role，不用动每个用户

    数据权限范围（data_scope）：
        ALL           —— 全部数据（超级管理员）
        DEPT          —— 本部门数据
        DEPT_AND_SUB  —— 本部门及下级部门
        SELF          —— 仅本人数据
        CUSTOM        —— 自定义组织（通过 custom_data_organizations 指定）
    """

    DATA_SCOPE_CHOICES = (
        ('ALL', '全部数据'),
        ('DEPT', '本部门'),
        ('DEPT_AND_SUB', '本部门及下级'),
        ('SELF', '仅本人'),
        ('CUSTOM', '自定义'),
    )

    name = models.CharField(max_length=64, unique=True, verbose_name='角色名称')
    code = models.CharField(max_length=64, unique=True, verbose_name='角色编码')
    description = models.CharField(max_length=256, blank=True, default='', verbose_name='描述')
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles', verbose_name='权限列表')
    menus = models.ManyToManyField(Menu, blank=True, related_name='roles', verbose_name='菜单可见')
    data_scope = models.CharField(max_length=16, choices=DATA_SCOPE_CHOICES, default='SELF', verbose_name='数据范围')

    class Meta:
        verbose_name = '角色'
        verbose_name_plural = '角色'

    def __str__(self):
        return self.name


# 角色在 CUSTOM 模式下，可以指定具体可见哪些组织
Role.add_to_class(
    'custom_data_organizations',
    models.ManyToManyField(
        'Organization', blank=True, related_name='roles_with_custom_scope', verbose_name='自定义数据范围组织'
    )
)


# ─────────────────────────────────────────────────────────────────
# 用户-角色 关联
# ─────────────────────────────────────────────────────────────────

class UserRole(models.Model):
    """
    用户-角色 多对多中间表。

    Django 自带的 auth.User.role 是一对多（一个用户一个角色）。
    这里扩展为多对多（一个用户可以有多个角色）。
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='绑定时间')

    class Meta:
        unique_together = ('user', 'role')
        verbose_name = '用户角色'
        verbose_name_plural = '用户角色'

    def __str__(self):
        return f"{self.user} → {self.role}"


# ─────────────────────────────────────────────────────────────────
# 组织（用于数据权限隔离）
# ─────────────────────────────────────────────────────────────────

class Organization(models.Model):
    """
    组织/部门 —— 用于数据权限隔离。

    数据权限的工作原理：
        —— 每个数据记录有 owner_organization（归属组织）
        —— 用户属于某个 Organization（通过 UserOrganization）
        —— Role 有 data_scope，决定用户能看哪些组织的数据
        —— 查询时动态拼接 .filter(owner_organization__in=allowed_orgs)
    """

    name = models.CharField(max_length=64, verbose_name='组织名称')
    code = models.CharField(max_length=64, unique=True, verbose_name='组织编码')
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.CASCADE, related_name='children', verbose_name='上级组织'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    leader = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='lead_organizations', verbose_name='负责人'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '组织'
        verbose_name_plural = '组织'
        ordering = ['order', 'id']

    def __str__(self):
        return self.name

    def get_ancestors(self):
        """获取所有上级组织（包含自己）"""
        ancestors = []
        current = self
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """获取所有下级组织（包含自己）"""
        descendants = [self]
        for child in self.children.all():
            descendants.extend(child.get_descendants())
        return descendants


# ─────────────────────────────────────────────────────────────────
# 用户-组织 关联
# ─────────────────────────────────────────────────────────────────

class UserOrganization(models.Model):
    """
    用户-组织 多对多关联，支持多组织和主组织标记。

    一个用户可以属于多个组织（如同时属于「总公司」和「研发部」）。
    is_primary=True 表示主组织（用于数据权限的默认归属）。
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_organizations')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='user_organizations')
    is_primary = models.BooleanField(default=False, verbose_name='是否主组织')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'organization')
        verbose_name = '用户组织'
        verbose_name_plural = '用户组织'

    def __str__(self):
        mark = ' (主)' if self.is_primary else ''
        return f"{self.user} → {self.organization}{mark}"
