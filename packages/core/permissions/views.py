"""
RBAC 权限控制实现
══════════════════════════════════════════════════════════════════

提供三种权限控制方式：

    1. RBACPermission —— DRF 权限类（类级别声明）
    2. rbac_permission —— 函数式装饰器（推荐，更直观）
    3. RBACPermissionByCode —— 基于权限码的精确权限检查

══════════════════════════════════════════════════════════════════

面试要点：

Q: DRF 权限检查的执行流程？
A:
    1. 经过所有 Middleware（SessionMiddleware 等）
    2. Authentication（SessionAuthentication / TokenAuthentication）
       → 从请求中提取 user
    3. Permission.check_permission(request, self)
       → 依次执行 permission_classes 中的每个权限类
       → 有一个返回 False/403 即拒绝访问
    4. Throttling（限流）
    5. 执行 ViewSet 的 get_queryset() / list() 等

Q: 为什么用装饰器而不是数据库配置？
A:
    - 数据库配置：改了代码要同步改数据库，git 追踪不完整
    - 装饰器：代码即权限定义，改动和代码一起 review

Q: 数据权限（组织隔离）怎么实现？
A:
    在 ViewSet.get_queryset() 中：
        1. 查用户的所有角色
        2. 看每个角色的 data_scope
        3. ALL → 不限制
        4. DEPT → filter(owner_organization__in=user_orgs)
        5. SELF → filter(created_by=user)
"""

import re
import functools
from django.db.models import Q
from rest_framework import permissions


# ─────────────────────────────────────────────────────────────────
# 1. RBACPermission —— DRF 权限类（URL 匹配模式）
# ─────────────────────────────────────────────────────────────────

class RBACPermission(permissions.BasePermission):
    """
    基于 URL 匹配的 DRF 权限类。

    检查逻辑：
        1. 未登录 → 拒绝
        2. 超级用户 → 放行
        3. 从 Permission 表查匹配当前 URL + HTTP Method 的记录
        4. 查用户是否拥有该 Permission
        5. 没有找到匹配的 Permission 记录 → 默认允许（向后兼容）

    配置方式（settings.py）：
        REST_FRAMEWORK = {
            'DEFAULT_PERMISSION_CLASSES': [
                'ram_core.permissions.RBACPermission',
            ],
        }
    """

    def has_permission(self, request, view):
        """每次请求前检查"""
        if not request.user or not request.user.is_authenticated:
            return False

        # 超级用户全权限
        if request.user.is_superuser:
            return True

        url_path = request.path
        http_method = request.method.upper()

        # 查找匹配的 Permission
        matched = self._find_matching_permission(url_path, http_method)

        # 没有找到 → 默认允许（避免需要给所有接口配权限）
        if not matched:
            return True

        return self._user_has_permission(request.user, matched)

    def _find_matching_permission(self, url_path, http_method):
        """
        查找匹配当前 URL 和 HTTP Method 的 Permission 记录。

        匹配算法：
            1. 精确匹配 url_pattern + http_method
            2. url_pattern 支持通配符 *（如 /api/article/*）
            3. http_method 为 ANY 时匹配所有方法
        """
        # 清理 URL 末尾的斜杠
        path = url_path.rstrip('/')

        from .models import Permission

        perms = Permission.objects.filter(is_active=True).filter(
            Q(http_method='ANY') | Q(http_method=http_method)
        )

        for perm in perms:
            pattern = perm.url_pattern.rstrip('/') if perm.url_pattern else ''
            if not pattern:
                continue

            # 转换为正则：* → .* ，{id} → \d+
            regex = self._url_to_regex(pattern)
            if re.match(regex, path):
                return perm

        return None

    def _url_to_regex(self, pattern):
        """URL 模式转正则表达式"""
        pattern = pattern.replace('*', '__STAR__')
        pattern = re.escape(pattern)
        pattern = pattern.replace('__STAR__', '[^/]+')
        # {pk} 或 {id} 转换为数字匹配
        pattern = re.sub(r'\\\{[^}]+\\\}', r'\\d+', pattern)
        if not pattern.endswith('$'):
            pattern = pattern + '(?:/.*)?$'
        return pattern

    def _user_has_permission(self, user, permission):
        """检查用户是否拥有指定权限"""
        from .models import Role

        # 用户拥有的所有角色
        user_roles = Role.objects.filter(user_roles__user=user).distinct()
        return permission.roles.filter(id__in=user_roles.values_list('id', flat=True)).exists()


# ─────────────────────────────────────────────────────────────────
# 2. rbac_permission —— 函数式装饰器（推荐用法）
# ─────────────────────────────────────────────────────────────────

class RBACPermissionByCode(permissions.BasePermission):
    """
    基于权限码（code）的精确权限检查。

    相比 URL 匹配的优势：
        —— 代码即权限，git 追踪完整
        —— 不依赖数据库 Permission 表（权限定义在代码里）
        —— 改了 API URL 不需要同步改权限记录

    用法（ViewSet）：
        class ArticleViewSet(ModelViewSet):
            permission_classes = [RBACPermissionByCode]
            # 每个 action 对应的权限码
            permission_code_map = {
                'list':   'article:list',
                'create': 'article:create',
                'update': 'article:update',
                'destroy':'article:delete',
            }
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # 从 ViewSet 获取当前 action
        action = getattr(view, 'action', None)
        if not action:
            return True  # 非 ViewSet 视图默认放行

        # 获取权限码映射
        code_map = getattr(view, 'permission_code_map', {}) or {}

        # 没有配置权限码 → 默认允许
        if not code_map or action not in code_map:
            return True

        permission_code = code_map[action]

        # 数据库查询用户是否拥有该权限码
        from .models import Permission, Role

        user_roles = Role.objects.filter(user_roles__user=request.user).distinct()
        return Permission.objects.filter(
            code=permission_code,
            roles__in=user_roles,
            is_active=True
        ).exists()


def rbac_permission(*codes):
    """
    函数式权限装饰器。

    用法（替代 permission_code_map）：
        @action(methods=['GET'], url_path='list')
        @rbac_permission('article:list')
        def list(self, request):
            ...

        @action(methods=['POST'])
        @rbac_permission('article:create')
        def create(self, request):
            ...

    效果：当前 action 需要拥有列表中任一权限码即可访问。
    """
    def decorator(func_or_viewset):
        # 支持装饰 ViewSet 的 action 或装饰整个 ViewSet 类
        if hasattr(func_or_viewset, 'cls'):  # 是 action 函数
            # action 的 permission 已经在函数属性上设置
            # 这里把需要的权限码加进去
            _mark_viewset_permission(func_or_viewset.cls, func_or_viewset.actions, codes)
        return func_or_viewset

    return decorator


def _mark_viewset_permission(viewset_cls, actions, codes):
    """
    内部方法：标记 ViewSet 的 action 需要的权限码。

    这个方法把装饰器收集到的权限码，
    写入 ViewSet 的 __init__ 或通过类属性传递。
    """
    # 简化处理：通过类属性存储
    if not hasattr(viewset_cls, '_rbac_action_codes'):
        viewset_cls._rbac_action_codes = {}
    for action in actions:
        viewset_cls._rbac_action_codes[action] = codes


# ─────────────────────────────────────────────────────────────────
# 3. DataScopeFilter —— 数据权限过滤
# ─────────────────────────────────────────────────────────────────

class DataScopeFilter:
    """
    数据权限过滤器（Mixin）。

    用法（作为基类混入 ViewSet）：
        class ArticleViewSet(DataScopeFilter, ModelViewSet):
            ...

    在 get_queryset() 中根据用户角色的 data_scope 自动过滤数据。

    data_scope 规则：
        ALL          → 不过滤（看到全部）
        DEPT         → 只看本部门数据
        DEPT_AND_SUB → 看本部门及下级部门
        SELF         → 只看自己创建的
        CUSTOM       → 只看 custom_data_organizations 指定的
    """

    # 子类可以覆盖这个属性来指定哪些字段用于数据权限过滤
    owner_field = 'owner_organization'
    creator_field = 'created_by'

    def get_queryset(self):
        """
        重写 get_queryset()，自动拼接数据权限过滤条件。
        """
        queryset = super().get_queryset()
        user = self.request.user

        if not user or not user.is_authenticated:
            return queryset.none()

        # 超级用户不过滤
        if user.is_superuser:
            return queryset

        # 查用户的所有角色，合并数据权限
        allowed_orgs = set()
        see_all = False
        see_self = False

        from .models import Role, UserOrganization

        roles = Role.objects.filter(user_roles__user=user).distinct()

        for role in roles:
            if role.data_scope == 'ALL':
                see_all = True
                break
            elif role.data_scope == 'SELF':
                see_self = True
            elif role.data_scope in ('DEPT', 'DEPT_AND_SUB', 'CUSTOM'):
                # 获取用户所属组织
                user_orgs = UserOrganization.objects.filter(user=user).values_list('organization_id', flat=True)

                if role.data_scope == 'DEPT':
                    allowed_orgs.update(user_orgs)
                elif role.data_scope == 'DEPT_AND_SUB':
                    from .models import Organization
                    for org_id in user_orgs:
                        try:
                            org = Organization.objects.get(pk=org_id)
                            allowed_orgs.update(org.get_descendants())
                        except Exception:
                            pass
                elif role.data_scope == 'CUSTOM':
                    custom_orgs = role.custom_data_organizations.values_list('id', flat=True)
                    allowed_orgs.update(custom_orgs)

        # 拼接过滤条件
        if see_all:
            return queryset

        if see_self:
            return queryset.filter(**{self.creator_field: user})

        if allowed_orgs:
            return queryset.filter(**{f'{self.owner_field}__in': allowed_orgs})

        # 没有角色或没有配置数据范围 → 只看自己的
        return queryset.filter(**{self.creator_field: user})
