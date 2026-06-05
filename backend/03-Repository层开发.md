# 03 - 数据访问层开发（Django Manager 模式）

## 适用场景
Model 定义完成后，封装数据查询逻辑。所有数据库查询通过 Manager 或 Service 层直接调用 ORM。

## 关联原则
- 原则3：关注点分离 — 查询逻辑集中在 Manager，不散落在 View 和 Service
- 原则1：SRP — 一个 Manager 只管一个 Model 的查询封装

## 核心规则
1. **用 Django Manager 封装查询逻辑**（Django 标准实践，不引入额外抽象层）
2. **Manager 方法返回 QuerySet**（支持链式调用，与 DRF Filter/分页无缝配合）
3. **Manager 不包含业务逻辑**（不判断权限、不校验数据、不写复杂条件分支）
4. **软删除过滤统一在 BaseManager**（避免每个查询手写 `is_deleted=False`）

## 设计对比

| | ABC + Generic + DI（原方案） | Django Manager（优化后） |
|---|---|---|
| 每个 Model 新增代码 | ~45 行（Interface + Impl + DI） | ~10 行（Manager 类） |
| 测试隔离方式 | 必须 Mock Repository | Django TestCase 事务回滚，零 Mock |
| Django 生态对齐 | 无先例，类 Java 风格 | Django 标准实践 |
| Service 调用方式 | 构造函数注入 `user_repo` | 直接调 `User.objects.active()` |
| 链式查询支持 | 不支持（返回具体类型） | 原生支持（返回 QuerySet） |

## 开发步骤

### 步骤 1：创建 BaseManager（软删除统一过滤）

文件：`apps/common/managers.py`

```python
from django.db import models


class BaseManager(models.Manager):
    """统一过滤软删除记录"""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def with_deleted(self):
        """获取全部记录（含已删除），仅审计等特殊场景使用"""
        return super().get_queryset()
```

### 步骤 2：Model 层挂载 Manager + 定义查询方法

文件：`apps/rbac/models.py`（扩展现有 Model）

```python
from django.db import models
from apps.common.base_model import BaseModel
from apps.common.managers import BaseManager


class UserManager(BaseManager):
    """User 查询封装"""

    def active(self):
        return self.filter(is_active=True)

    def by_email(self, email: str):
        return self.filter(email=email)

    def by_username(self, username: str):
        return self.filter(username=username)

    def by_role(self, role_id: int):
        return self.filter(
            userrole__role_id=role_id
        ).select_related()


class User(BaseModel):
    """用户 - 系统用户"""
    username = models.CharField(max_length=150, unique=True, verbose_name="用户名")
    email = models.EmailField(unique=True, verbose_name="邮箱")
    password_hash = models.CharField(max_length=255, verbose_name="密码哈希")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    last_login_at = models.DateTimeField(null=True, blank=True, verbose_name="最后登录")

    objects = UserManager()  # 挂载自定义 Manager

    class Meta:
        db_table = 'rbac_users'
        verbose_name = '用户'
        indexes = [
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(fields=['username'], name='idx_user_username'),
        ]


class RoleManager(BaseManager):
    """Role 查询封装"""

    def by_code(self, code: str):
        return self.filter(code=code)

    def with_permissions(self, role_id: int):
        return self.filter(id=role_id).prefetch_related(
            'rolepermission_set__permission'
        )


class Role(BaseModel):
    """角色 - 权限的集合"""
    name = models.CharField(max_length=100, unique=True, verbose_name="角色名")
    code = models.CharField(max_length=50, unique=True, verbose_name="角色编码")
    description = models.TextField(default="", verbose_name="描述")

    objects = RoleManager()

    class Meta:
        db_table = 'rbac_roles'


class Permission(BaseModel):
    """权限 - 最小权限单元"""
    name = models.CharField(max_length=100, verbose_name="权限名")
    code = models.CharField(max_length=100, unique=True, verbose_name="权限编码")
    resource = models.CharField(max_length=100, verbose_name="资源")
    action = models.CharField(max_length=50, choices=[
        ('create', '创建'), ('read', '读取'),
        ('update', '更新'), ('delete', '删除'),
    ], verbose_name="操作")

    objects = BaseManager()  # 无特殊查询，直接用 BaseManager

    class Meta:
        db_table = 'rbac_permissions'
        unique_together = [['resource', 'action']]
```

### 步骤 3：Service 层调用方式

Manager 封装后，Service 直接使用链式调用，无需依赖注入：

```python
# apps/rbac/services/user_service.py
from apps.rbac.models import User

class UserService:
    """用户业务逻辑"""

    def get_active_users(self):
        # 链式调用：Manager过滤 + 额外条件
        return User.objects.active().filter(department_id=dept_id)

    def find_by_email(self, email: str):
        return User.objects.by_email(email).first()

    def list_by_role(self, role_id: int):
        return User.objects.by_role(role_id)
```

### 步骤 4：复杂查询直接写在 Service 层

对于跨 Model 的复杂查询（涉及多表 join、聚合、子查询），直接在 Service 中写 ORM，不需要为每个查询都定义 Manager 方法：

```python
# 复杂查询示例：无需再定义 Manager 方法
from django.db.models import Count, Q

class ReportService:
    def get_user_stats_by_department(self):
        return (
            User.objects
            .values('department_id')
            .annotate(
                total=Count('id'),
                active=Count('id', filter=Q(is_active=True)),
            )
        )
```

## 查询优化速查
| 场景 | 方法 |
|------|------|
| ForeignKey（多对一） | `select_related('field')` |
| 反向 FK / M2M | `prefetch_related('related_set')` |
| 只要部分字段 | `only('id', 'name')` / `defer('large_field')` |
| 分页 | DRF `PageNumberPagination`（自动处理） |
| 聚合 | `annotate(total=Count('id'))` |
| 子查询 | `Subquery` / `OuterRef` |

## 反模式（禁止）
- ❌ 为每个查询都定义一个 Manager 方法 → 高频复用查询才封装，一次性查询直接在 Service 写
- ❌ Manager 方法里写 `if/else` 业务分支 → 业务逻辑在 Service 层
- ❌ 忘记 `select_related` / `prefetch_related` → N+1 查询
- ❌ 在 View 层直接写复杂 ORM → 至少放到 Service 层

## 自检清单
- [ ] 所有 Model 挂了 `BaseManager`（统一软删除过滤）？
- [ ] 高频复用查询封装为 Manager 方法？
- [ ] 外键查询用了 `select_related` 吗？
- [ ] 一对多/多对多查询用了 `prefetch_related` 吗？
- [ ] View 层不直接写复杂 ORM（至少经过 Service）？
- [ ] Manager 方法内没有 `if/else` 业务判断？
- [ ] 删除操作用的软删除（不是 `obj.delete()`）？
