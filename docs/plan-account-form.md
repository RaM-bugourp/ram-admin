# 账户表单功能开发规划

> 时间: 2026-06-05 | 参考: docs/backend/02-06 + docs/frontend/13-14

---

## 当前状态

| 层 | 已完成 | 待开发 |
|---|---|---|
| Model | User, BaseModel, BaseManager | Role, Permission, UserRole, RolePermission, Menu, Department |
| Manager | UserManager | 各 Model Manager |
| Service | 无 | UserService 全套 CRUD |
| Serializer | 无（AuthView 内联） | UserCreate/Update/OutputSerializer |
| ViewSet | AuthViewSet（登录/登出） | UserViewSet（CRUD） |
| URLs | `/api/auth/*` | `/api/rbac/users/*` |
| 前端 Views | Login, Dashboard, 403, 404 | 用户列表/表单页 |
| 前端 API | auth.ts | user.ts |

## 开发分层计划

### Phase 1 — 后端数据层（Model + Manager）

**文件:** `apps/rbac/models.py`

新增模型:
```
Role(name, code, description)
Permission(name, code, resource, action)
UserRole(user FK, role FK)          — 中间表
RolePermission(role FK, permission FK)  — 中间表
Menu(name, path, icon, parent FK, sort, permission_code)
Department(name, parent FK, sort)   — 自引用树
```

**文件:** `apps/common/managers.py` (扩展)

新增 Manager:
```
RoleManager   — by_code()
PermissionManager — by_resource()
MenuManager   — roots()
DepartmentManager — roots(), children_of()
```

**迁移:** `makemigrations + migrate`

---

### Phase 2 — 后端业务层（Service + Serializer + ViewSet）

**Service** `apps/rbac/services/user_service.py`:
- `list_users(page, page_size, search)` → 分页列表
- `get_user_detail(user_id)` → 详情
- `create_user(data, operator_id)` → 创建+角色分配
- `update_user(user_id, data)` → 更新
- `delete_user(user_id)` → 软删除
- `reset_password(user_id, new_password)` → 密码重置

**Serializer** `apps/rbac/serializers/user_serializers.py`:
- `UserCreateSerializer` — 创建输入
- `UserUpdateSerializer` — 更新输入
- `UserResetPasswordSerializer` — 密码重置输入
- `UserOutputSerializer` — 输出

**ViewSet** `apps/rbac/views/user_views.py`:
- `GET /api/rbac/users/` — 列表（分页+搜索）
- `POST /api/rbac/users/` — 创建
- `GET /api/rbac/users/{id}/` — 详情
- `PUT /api/rbac/users/{id}/` — 更新
- `DELETE /api/rbac/users/{id}/` — 软删除
- `POST /api/rbac/users/{id}/reset-password/` — 密码重置

**URLs** `apps/rbac/urls_user.py` → 注册到 `config/urls.py`

---

### Phase 3 — 前端（Types + API + Pages）

**Types** `api/types/user.ts`:
- `UserCreateInput` / `UserUpdateInput` / `UserOutput`
- 运行时校验函数

**API** `api/modules/user.ts`:
- `list` / `getById` / `create` / `update` / `delete` / `resetPassword`

**Pages** `views/system/user/`:
- `UserListView.vue` — 搜索栏 + Arco Table + 分页 + 状态标签
- `UserFormDialog.vue` — 创建/编辑弹窗表单

**Router:** 添加 `/system/user` 路由

---

## 数据流示意

```
┌─ UserListView ────────────────────────────────────────┐
│  SearchBar → onSearch → fetchData → userApi.list()    │
│  Arco Table ← tableData ← userApi response            │
│  "新建" btn → UserFormDialog (visible=true)            │
│  "编辑" btn → UserFormDialog (user prop set)           │
│  "删除" btn → confirm → userApi.delete()              │
└───────────────────────────────────────────────────────┘
         ↓ Axios → /api/rbac/users/*
         ↓
┌─ ViewSet ────────────────────────────────────────────┐
│  list/create/retrieve/update/destroy                  │
│  @action: reset_password                              │
└──────────────────────────↓───────────────────────────┘
         ↓ delegate to Service
┌─ UserService ────────────────────────────────────────┐
│  business logic, validation, transaction              │
└──────────────────────────↓───────────────────────────┘
         ↓ ORM via Model.objects (Manager)
┌─ Models ─────────────────────────────────────────────┐
│  User, Role, Permission, UserRole, RolePermission     │
└───────────────────────────────────────────────────────┘
```

## 实施顺序

1. ✅ **Phase 1** — Model + Manager + Migration（数据基础）
2. ✅ **Phase 2** — Service + Serializer + ViewSet + URLs（API 就绪）
3. ✅ **Phase 3** — Frontend Types + API + Pages（前端就绪）
