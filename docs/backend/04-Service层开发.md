# 04 - Service 层开发

## 适用场景
实现业务逻辑层。所有业务规则、流程编排、跨领域协调在此层。

## 关联原则
- 原则1：SRP — 一个 Service 一个业务领域，一个方法一个操作
- 原则3：关注点分离 — 不含 HTTP 上下文（不访问 request/Response）
- 原则7：一致性优先 — 核心写操作用 `@transaction.atomic`

## 核心规则
1. **Service 直接使用 Django ORM**（通过 Model.objects Manager，无需额外 Repository 层）
2. **每个方法 ≤ 30 行**，超过必须拆分
3. **方法名不包含 "and"/"or"** — 做多件事就拆
4. **不返回 Response、不访问 request**（参数传入 user_id 等）
5. **Service 可以依赖同层 Service**（允许跨领域调用，避免过度 Orchestrator）
6. **异常统一用 `ErrorCode` 枚举**（见 20-错误码体系）

## 设计优化说明

| | 原方案（DI + Orchestrator） | 优化后 |
|---|---|---|
| 依赖注入 | `__init__(self, user_repo=UserRepository())` | 直接用 `User.objects.xxx()` |
| 跨领域调用 | 必须建 Orchestrator | Service 可直接依赖 Service |
| 错误抛出 | `BusinessError(message="...", code="...")` | `raise ErrorCode.ROLE_NOT_FOUND.as_exc()` |
| 典型场景 | 用户注册 = 3 个类 | 用户注册 = 1 个 Service |

**Orchestrator 使用准则**：只有当业务流程涉及 **≥4 个 Service** 且有明确的顺序依赖时才引入 Orchestrator。绝大多数场景（2-3 个 Service 协调）直接在 Service 中依赖即可。

## 开发步骤

### 步骤 1：定义 Service 类

文件：`apps/rbac/services/user_service.py`

```python
import logging
from django.db import transaction
from apps.common.exceptions import ErrorCode
from apps.rbac.models import User, UserRole

logger = logging.getLogger(__name__)


class UserService:
    """用户业务逻辑"""

    @transaction.atomic
    def create_user(self, data: dict, operator_id: int) -> dict:
        """
        创建用户（含角色分配 + 审计）。

        Args:
            data: 用户数据（username/email/password/role_ids/department_id）
            operator_id: 操作人ID

        Returns:
            创建的用户摘要信息

        Raises:
            ErrorCode.ADMIN_REQUIRES_DEPARTMENT
        """
        # 1. 业务校验
        if 'admin' in data.get('role_codes', []):
            if not data.get('department_id'):
                raise ErrorCode.ADMIN_REQUIRES_DEPARTMENT.as_exc()

        # 2. 创建用户
        user = User.objects.create(
            username=data['username'],
            email=data['email'],
            password_hash=self._hash_password(data['password']),
        )

        # 3. 分配角色（Service 内直接操作关联表，简单逻辑不拆 Service）
        if data.get('role_ids'):
            for role_id in data['role_ids']:
                UserRole.objects.create(user_id=user.id, role_id=role_id)

        # 4. 记录审计（跨 Service 调用 — 合理的 Service 间依赖）
        AuditService().log_action(
            action='user.create',
            target_id=user.id,
            operator_id=operator_id,
            detail={'username': user.username},
        )

        # 5. 事务提交后发送通知
        transaction.on_commit(
            lambda: NotificationService().send_welcome_email(user.email)
        )

        logger.info("User created", extra={"user_id": user.id, "username": user.username})
        return {'id': user.id, 'username': user.username, 'email': user.email}

    def _hash_password(self, password: str) -> str:
        """密码哈希 - 独立方法"""
        from django.contrib.auth.hashers import make_password
        return make_password(password)

    def get_active_users(self, department_id: int = None):
        """获取活跃用户列表"""
        qs = User.objects.active()
        if department_id:
            qs = qs.filter(department_id=department_id)
        return qs

    def find_by_email(self, email: str):
        """按邮箱查用户"""
        return User.objects.by_email(email).first()
```

### 步骤 2：权限业务 Service

文件：`apps/rbac/services/permission_service.py`

```python
import logging
from django.db import transaction
from apps.common.exceptions import ErrorCode
from apps.rbac.models import Role, Permission, User

logger = logging.getLogger(__name__)


class RolePermissionService:
    """角色权限业务"""

    @transaction.atomic
    def assign_permissions_to_role(
        self, role_id: int, permission_ids: list, operator_id: int
    ):
        """给角色分配权限（原子操作 + 审计）"""
        role = Role.objects.filter(id=role_id).first()
        if not role:
            raise ErrorCode.ROLE_NOT_FOUND.as_exc()

        # 记录审计（同一事务内）
        AuditService().log_action(
            action='role.assign_permissions',
            target_id=role_id,
            operator_id=operator_id,
            detail={'permission_ids': permission_ids},
        )

        role.permissions.set(permission_ids)

        # 清理权限缓存（事务提交后）
        transaction.on_commit(lambda: cache.delete(f'role_perms:{role_id}'))

    def check_permission(self, user_id: int, permission_code: str) -> bool:
        """检查用户是否有某权限"""
        return User.objects.filter(
            id=user_id,
            userrole__role__rolepermission__permission__code=permission_code,
        ).exists()
```

### 步骤 3：跨领域编排 — Orchestrator（仅在 ≥4 Service 时使用）

```python
class WorkflowOrchestrator:
    """
    审批流编排器。
    仅在业务流程涉及 ≥4 个 Service 且有明确顺序依赖时使用。
    普通 2-3 个 Service 协调直接在 Service 内完成。
    """

    def __init__(self):
        self.user_service = UserService()
        self.audit_service = AuditService()
        self.notification_service = NotificationService()
        self.approval_service = ApprovalService()

    @transaction.atomic
    def process_approval(self, request_id: int, operator_id: int):
        approval = self.approval_service.approve(request_id, operator_id)
        self.audit_service.log_action(
            action='approval.process',
            target_id=request_id,
            operator_id=operator_id,
        )
        transaction.on_commit(
            lambda: self.notification_service.send_approval_result(approval)
        )
        return approval
```

## 反模式（禁止）
- ❌ Service 访问 `request.user` → 从参数传入 `user_id`/`operator_id`
- ❌ Service 返回 `Response(...)` → 返回 dict / dataclass
- ❌ 一个方法处理多个独立业务 → 拆分为多个方法
- ❌ `except Exception` 吞异常 → 用 `ErrorCode` 枚举或让上层处理
- ❌ 为 2 个 Service 的调用强行建 Orchestrator → 直接在 Service 里依赖即可

## 自检清单
- [ ] 所有方法 ≤ 30 行？
- [ ] 方法名不含 "and"/"or"？
- [ ] 核心写操作加了 `@transaction.atomic`？
- [ ] 不访问 `request` 对象（参数传入）？
- [ ] 不直接返回 DRF Response？
- [ ] 异常用 `ErrorCode` 枚举（非裸字符串 code）？
- [ ] Service 间依赖合理（无循环依赖）？
- [ ] Orchestrator 仅在 ≥4 Service 时使用？
