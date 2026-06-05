# 02 - Model 层开发

## 适用场景
定义数据库表结构。每次新增业务实体时使用本 Prompt。

## 关联原则
- 原则1：SRP — 一个 Model 只描述一个实体
- 原则3：关注点分离 — Model 不包含业务逻辑，纯数据结构
- 原则7：一致性优先 — 核心数据用唯一约束/外键约束

## 核心规则
1. **继承 BaseModel**（含 created_at/updated_at/is_deleted）
2. **外键必须加索引**（`db_index=True` 或显式 `Meta.indexes`）
3. **软删除**用 `is_deleted`，不真删
4. **字符串字段**不允许 null（用 `default=""`）
5. **枚举**用 `CharField + choices`，不用数据库 ENUM 类型

## 开发步骤

### 步骤 1：分析业务实体 → 生成 ER 关系

输入业务需求，先输出 ER 关系：
```
模块: RBAC
├── User (用户) ──1:N── UserRole (用户-角色) ──N:1── Role (角色)
│   └── 1:1 ── UserProfile (用户资料)
└── Role ──1:N── RolePermission ──N:1── Permission (权限)
    └── N:1 ── Menu (菜单)
```

### 步骤 2：生成每个 Model

以 `apps/rbac/models.py` 为例：

```python
from django.db import models
from apps.common.base_model import BaseModel

class User(BaseModel):
    """用户 - 系统用户"""
    username = models.CharField(max_length=150, unique=True, verbose_name="用户名")
    email = models.EmailField(unique=True, verbose_name="邮箱")
    password_hash = models.CharField(max_length=255, verbose_name="密码哈希")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    last_login_at = models.DateTimeField(null=True, blank=True, verbose_name="最后登录")

    class Meta:
        db_table = 'rbac_users'
        verbose_name = '用户'
        indexes = [
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(fields=['username'], name='idx_user_username'),
        ]

class Role(BaseModel):
    """角色 - 权限的集合"""
    name = models.CharField(max_length=100, unique=True, verbose_name="角色名")
    code = models.CharField(max_length=50, unique=True, verbose_name="角色编码")
    description = models.TextField(default="", verbose_name="描述")

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

    class Meta:
        db_table = 'rbac_permissions'
        unique_together = [['resource', 'action']]

class UserRole(BaseModel):
    """用户角色关联（中间表）"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_index=True)

    class Meta:
        db_table = 'rbac_user_roles'
        unique_together = [['user', 'role']]

class RolePermission(BaseModel):
    """角色权限关联（中间表）"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_index=True)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, db_index=True)

    class Meta:
        db_table = 'rbac_role_permissions'
        unique_together = [['role', 'permission']]
```

### 步骤 3：生成迁移并验证

```bash
python manage.py makemigrations rbac
python manage.py sqlmigrate rbac 0001  # 预览 SQL
python manage.py migrate
```

## 反模式（禁止）
- ❌ `CharField(null=True)` → ✅ `CharField(default="")`
- ❌ `TextField(null=True)` → ✅ `TextField(default="")`
- ❌ 用数据库 ENUM → ✅ `CharField(max_length=50, choices=XXX)`
- ❌ 外键不加索引 → ✅ `db_index=True` 或 `Meta.indexes`
- ❌ `CASCADE` 不思考就加 → ✅ 明确是否需要 PROTECT/SET_NULL
- ❌ JSON 字段存关联数据 → ✅ 建关联表

## 自检清单
- [ ] 所有 Model 继承 `BaseModel`？
- [ ] 所有外键都有索引？
- [ ] 字符串字段默认值用 `""`（不是 `null`）？
- [ ] 没有数据库 ENUM 类型？
- [ ] 多对多关系用了中间表（不是 ManyToManyField）？
- [ ] 表名是复数形式（`db_table = 'rbac_users'`）？
- [ ] 软删除用 `is_deleted` 字段？
- [ ] 唯一约束在数据库层面也用 `unique=True` 或 `unique_together`？
