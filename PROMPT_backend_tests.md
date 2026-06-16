# Prompt: 为 ram-adminx 后端编写完整测试套件

> 将此 prompt 交给 Agent 执行，目标是为 Django 5.2 + DRF 后端添加 pytest 测试。

## 1. 环境准备

在 `backend/` 目录下操作：

```bash
cd C:/Users/19635/Desktop/ram-adminx/backend
```

安装测试依赖：

```bash
pip install pytest pytest-django pytest-cov coverage
```

## 2. 测试配置文件

**创建 `backend/pytest.ini`**：

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.dev
python_files = tests.py test_*.py *_tests.py
testpaths = apps
```

## 3. 测试目录结构

创建以下目录结构：

```
backend/apps/
├── conftest.py              # 全局 fixtures（API client、测试用户、测试角色）
├── common/
│   └── tests/
│       ├── __init__.py
│       ├── test_base_model.py     # BaseModel 软删除行为
│       ├── test_exceptions.py     # BusinessError + exception handler
│       └── test_managers.py       # BaseManager 过滤逻辑
├── rbac/
│   └── tests/
│       ├── __init__.py
│       ├── test_auth.py           # 登录/登出/CSRF/user-info
│       ├── test_user_crud.py      # 用户 CRUD + 权限校验
│       ├── test_role_crud.py      # 角色 CRUD + BOSS 唯一性
│       ├── test_permissions.py    # IsAdminOrReadOnly 各场景
│       ├── test_dashboard.py      # Dashboard 统计数据
│       ├── test_user_service.py   # UserService 单元测试
│       └── test_role_service.py   # RoleService 单元测试
└── ai/
    └── tests/
        ├── __init__.py
        ├── test_ai_failover.py    # CircuitBreaker + 故障转移
        ├── test_ai_service.py     # AIService（Mock 模式/频次限制）
        ├── test_ai_approval.py    # 两阶段审批工作流
        ├── test_agent_token.py    # HMAC-SHA256 Token 签发/验证
        └── test_ai_models.py      # AICallLog/AIApproval/Notification 模型
```

## 4. 全局 Fixtures（backend/apps/conftest.py）

所有测试共享以下 fixtures：

```python
import pytest
from django.test import Client
from django.urls import reverse
from apps.rbac.models import User, Role, UserRole

@pytest.fixture
def api_client():
    """返回 DRF APIClient，自动处理 CSRF"""
    from rest_framework.test import APIClient
    client = APIClient(enforce_csrf_checks=False)
    return client

@pytest.fixture
def root_user(db):
    """创建 root 角色 + root 用户"""
    role = Role.objects.create(name='管理员', code='root')
    user = User.objects.create_user(username='admin', email='admin@test.com', password='admin123')
    UserRole.objects.create(user=user, role=role)
    return user

@pytest.fixture
def boss_user(db):
    """创建 BOSS 角色 + BOSS 用户"""
    role = Role.objects.create(name='BOSS', code='boss', description='全局唯一管理员', is_unique=True)
    user = User.objects.create_user(username='boss001', email='boss@test.com', password='boss123')
    UserRole.objects.create(user=user, role=role)
    return user

@pytest.fixture
def normal_user(db):
    """创建普通用户"""
    role = Role.objects.create(name='普通用户', code='user')
    user = User.objects.create_user(username='user001', email='user@test.com', password='user123')
    UserRole.objects.create(user=user, role=role)
    return user

@pytest.fixture
def authed_client(api_client, root_user):
    """已登录 root 用户的 API client"""
    api_client.force_authenticate(user=root_user)
    return api_client, root_user

@pytest.fixture
def normal_client(api_client, normal_user):
    """已登录普通用户的 API client"""
    api_client.force_authenticate(user=normal_user)
    return api_client, normal_user
```

## 5. 各测试文件内容

### 5.1 `backend/apps/common/tests/test_base_model.py`

测试目标：
- `BaseModel` 自动填充 `created_at`, `updated_at`
- `soft_delete()` 设置 `is_deleted=True` 但不删除记录
- 验证 `updated_at` 在更新后变化

### 5.2 `backend/apps/common/tests/test_managers.py`

测试目标：
- `BaseManager.get_queryset()` 默认过滤 `is_deleted=False`
- `BaseManager.with_deleted()` 返回全部记录（含软删除）
- 验证软删除用户的 `UserManager` 查询行为

### 5.3 `backend/apps/common/tests/test_exceptions.py`

测试目标：
- `BusinessError` 构造正确
- `custom_exception_handler` 将 BusinessError 转为 `{error: {code, message}}` 格式
- 非 BusinessError 的 DRF 异常被正确包裹

### 5.4 `backend/apps/rbac/tests/test_auth.py`

测试目标（通过 API 端点测试）：

**test_login_success**:
- POST `/api/auth/login/` 正确用户名密码 → 200 + 包含 `data` + `data.roles` 非空

**test_login_failure**:
- 错误密码 → 401 + `error` 格式

**test_csrf_endpoint**:
- GET `/api/auth/csrf/` → 设置 `csrftoken` Cookie

**test_user_info**:
- 已登录用户 GET `/api/auth/user-info/` → 返回用户名/邮箱/角色列表

**test_user_info_unauthenticated**:
- 未登录用户 GET `/api/auth/user-info/` → 403

**test_soft_deleted_user_login**:
- 软删除用户尝试登录 → 401（backends.py 应过滤）

### 5.5 `backend/apps/rbac/tests/test_user_crud.py`

测试目标：

**test_list_users**:
- GET `/api/rbac/users/` → 200 + pagination 格式

**test_list_users_with_search**:
- 带 `?search=` 参数过滤 → 返回匹配结果

**test_list_users_pagination**:
- 带 `?page=&page_size=` → 正确分页

**test_create_user**:
- POST `/api/rbac/users/` 有效的创建数据 → 201 + 返回用户

**test_create_user_duplicate_username**:
- 重复用户名 → 409 + `DUPLICATE_USERNAME`

**test_create_user_duplicate_email**:
- 重复邮箱 → 409 + `DUPLICATE_EMAIL`

**test_create_user_as_normal_user**:
- 普通用户 POST 创建 → 403（权限校验）

**test_update_user**:
- PUT `/api/rbac/users/{id}/` → 200 + 字段已更新

**test_delete_user**:
- DELETE `/api/rbac/users/{id}/` → 200 + 用户被软删除（GET 列表不可见）

**test_delete_user_not_found**:
- 删除不存在的用户 → 404

**test_reset_password**:
- POST `/api/rbac/users/{id}/reset-password/` → 200 + 新密码可用

**test_get_user_detail**:
- GET `/api/rbac/users/{id}/` → 返回用户详情

### 5.6 `backend/apps/rbac/tests/test_role_crud.py`

测试目标：

**test_list_roles**:
- GET `/api/rbac/roles/` → 200 + 列表

**test_create_role**:
- POST 创建角色 → 201

**test_create_boss_role_unique**:
- 创建 `is_unique=True` 的 BOSS 角色 → 成功后再次创建应失败

**test_delete_system_role**:
- 删除 `root`/`boss`/`user` 系统角色 → 400 拒绝

**test_delete_normal_role**:
- 删除普通角色 → 200

**test_normal_user_cannot_create_role**:
- 普通用户创建角色 → 403

**test_update_role**:
- PUT 更新角色 → 200

### 5.7 `backend/apps/rbac/tests/test_permissions.py`

测试目标：

**test_admin_can_write**:
- root/boss 用户 POST/PUT/DELETE → 200

**test_normal_user_readonly**:
- 普通用户 GET → 200；POST/PUT/DELETE → 403

**test_unauthenticated_readonly**:
- 未登录用户 GET → 403（DRF IsAuthenticated 优先）

**test_role_permission_edge_cases**:
- 用户登录后删除其 root 角色 → 刷新后应该失去写权限（通过 `force_authenticate` + `logout` 模拟）

### 5.8 `backend/apps/rbac/tests/test_dashboard.py`

测试目标：

**test_dashboard_stats**:
- GET `/api/dashboard/stats/` → 200 + 返回 4 个统计字段（total_users, active_users, total_roles, total_assignments）

**test_dashboard_stats_accuracy**:
- 创建/删除用户/角色后 → 统计值应相应变化

### 5.9 `backend/apps/rbac/tests/test_user_service.py`

测试目标（直接测试 Service 层，不通过 HTTP）：

**test_list_users_pagination**:
- `UserService().list_users(page=1, page_size=10)` 返回正确分页

**test_list_users_search**:
- search 参数过滤正确

**test_create_user_success**:
- `create_user()` 返回 User 实例

**test_create_user_duplicate**:
- 重复用户名抛出 `BusinessError(code='DUPLICATE_USERNAME')`

**test_update_user_not_found**:
- 不存在的 user_id → `BusinessError(code='USER_NOT_FOUND')`

**test_delete_user_soft_delete**:
- `delete_user()` 后 `user.is_deleted == True`

### 5.10 `backend/apps/rbac/tests/test_role_service.py`

测试目标（直接测试 RoleService）：

**test_enforce_unique_role**:
- `enforce_unique_role()` 校验 BOSS 唯一性

**test_cannot_delete_system_role**:
- 删除 system role → BusinessError

### 5.11 `backend/apps/ai/tests/test_ai_failover.py`

测试目标：

**test_circuit_breaker_initial_state**:
- 新建熔断器 → `status == HEALTHY`, `can_use() == True`

**test_circuit_breaker_opens_after_threshold**:
- 连续失败 N 次 → `status == FAILED`, `can_use() == False`

**test_circuit_breaker_recovers**:
- 进入 FAILED 后等待 recovery_timeout → `can_use() == True`, `status == DEGRADED`

**test_circuit_breaker_records_success**:
- `record_success()` → `failures == 0`, `status == HEALTHY`

**test_circuit_breaker_thread_safety**:
- 并发调用 `record_failure()` 无竞态（通过 mock 测试）

**test_load_providers**:
- 模拟 settings.AI_PROVIDERS → 返回正确 ProviderConfig 列表

**test_get_active_providers**:
- 只返回已配置 Key 的 Provider

### 5.12 `backend/apps/ai/tests/test_ai_service.py`

测试目标：

**test_mock_mode**:
- 未配置任何 AI Provider → `AIService().chat()` 返回 mock 回复 + `provider='mock'`

**test_all_providers_fail**:
- 所有 Provider 都失败 → 抛出 `AIAllProvidersFailedError`

**test_rate_limit_root**:
- 超过 `AI_RATE_LIMIT_PER_ROOT` 次调用 → `AIRateLimitError`

**test_rate_limit_agent**:
- 超过 `AI_RATE_LIMIT_PER_AGENT` 次 → `AIRateLimitError`

**test_failover_chain**:
- 主 Provider 失败 → 自动切换到备用 Provider

### 5.13 `backend/apps/ai/tests/test_ai_approval.py`

测试目标：

**test_submit_approval**:
- Agent 提交审批 → status='pending'

**test_approve_approval**:
- Root 审批通过 → status='approved' → 自动执行 → status='executed'

**test_reject_approval**:
- Root 审批拒绝 → status='rejected'

**test_invalid_operation**:
- 提交不支持的 operation → 400

**test_create_user_via_approval**:
- 审批通过后的 create_user 自动执行 → 用户被创建

**test_approval_timeout**:
- 超时未审批 → status='timeout'

### 5.14 `backend/apps/ai/tests/test_agent_token.py`

测试目标：

**test_issue_token**:
- `AgentTokenService.issue()` 返回格式正确的 Token（`<exp>.<uid>.<agent_id>.<sig>`）

**test_verify_valid_token**:
- 签发后立即验证 → 返回正确 payload

**test_verify_expired_token**:
- 过期的 Token → 返回 `None`

**test_verify_tampered_token**:
- 篡改过的 Token（改签名/改过期时间）→ 返回 `None`

**test_unique_secret_per_token**:
- 不同 `SECRET_KEY` 下签发的 Token 互相不能验证

### 5.15 `backend/apps/ai/tests/test_ai_models.py`

测试目标：

**test_ai_call_log_creation**:
- 创建 `AICallLog` → 所有字段正确保存

**test_ai_approval_status_choices**:
- 验证 status 字段的 choices（pending/approved/rejected/timeout/executed/failed）

**test_notification_level_choices**:
- 验证 level 字段 choices（info/success/warning/error）

**test_soft_delete_inheritance**:
- AI 模型继承 BaseModel → 支持软删除

## 6. Mock 策略

对于 AI 测试（需要外部 HTTP 调用），使用 `unittest.mock.patch` 模拟：

```python
from unittest.mock import patch, MagicMock

# 模拟 ai_client.call_chat
@patch('apps.ai.services.ai_client.call_chat')
def test_failover(mock_call_chat, ...):
    mock_call_chat.side_effect = [AIProviderError('fail'), 'reply']
    ...
```

对于模拟 Provider 配置，使用 `@override_settings`：

```python
from django.test.utils import override_settings

@override_settings(AI_PROVIDERS=[...], AI_MOCK_WHEN_NO_KEY=False)
def test_something(...):
    ...
```

## 7. 执行与验证

```bash
cd C:/Users/19635/Desktop/ram-adminx/backend

# 安装依赖
pip install pytest pytest-django pytest-cov coverage

# 运行全部测试
python -m pytest apps/ -v

# 查看测试覆盖率
python -m pytest apps/ --cov=apps --cov-report=term --cov-report=html

# 仅运行特定测试文件
python -m pytest apps/rbac/tests/test_auth.py -v
python -m pytest apps/ai/tests/ -v
```

## 8. 验收标准

- [ ] 全部测试通过（`python -m pytest apps/ -v` 无 FAILED）
- [ ] 覆盖率 ≥ 80%（行覆盖率）
- [ ] 每个核心 API 端点至少有 1 个成功场景 + 1 个失败场景测试
- [ ] 每个权限层级（无登录/普通用户/admin/root）至少覆盖
- [ ] AI 熔断器的 3 种状态（HEALTHY → FAILED → DEGRADED）全部覆盖
- [ ] Mock 模式 + 真实故障转移两种路径都覆盖
- [ ] BOSS 唯一性、系统角色保护等业务规则全部覆盖
