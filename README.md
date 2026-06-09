# Ram-AdminX

> Django 5.2 + Vue 3 + Arco Design 现代化后台管理系统

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green)](https://djangoproject.com)
[![Vue](https://img.shields.io/badge/Vue-3.5-brightgreen)](https://vuejs.org)
[![Arco Design](https://img.shields.io/badge/Arco_Design-2.56-165dff)](https://arco.design/vue)

---

## 当前版本

**v0.3.0** — 三级角色体系 (root/user/BOSS) + 前端权限控制 + 实时仪表盘。

### 已实现

- **认证系统** — 自定义 User 模型（`AbstractBaseUser`）、Session + CSRF 双重保护
- **用户管理** — 列表分页搜索、创建/编辑/删除（软删除）、密码重置、多角色分配
- **角色管理** — 三级角色体系 (root/BOSS/user)，CRUD 完整支持，BOSS 全局唯一校验
- **权限控制** — `IsAdminOrReadOnly` 后端权限类 + 前端按钮按角色显隐（`isAdmin` getter）
- **仪表盘** — 实时统计（用户数/活跃用户/角色数/角色分配数）
- **分层架构** — ViewSet → Service → Manager → Model 四层解耦
- **前端页面** — 登录页、仪表盘（实时数据）、用户列表、角色列表、表单弹窗

### 规划中

菜单管理、权限粒度分配、操作日志、代码生成器

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Django 5.2 + Django REST Framework |
| 数据库 | SQLite（开发）→ PostgreSQL（生产） |
| 前端框架 | Vue 3 (Composition API) + TypeScript |
| UI 组件库 | Arco Design Vue 2.56 |
| 状态管理 | Vuex 4 |
| 路由 | Vue Router 4 |
| HTTP 客户端 | Axios（withCredentials + CSRF） |
| 构建工具 | Vite 6 |

---

## 项目结构

```
ram-adminx/
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py           # 公共配置（中间件、DRF、认证模型）
│   │   │   └── dev.py            # 开发环境覆盖
│   │   └── urls.py               # 根路由
│   ├── apps/
│   │   ├── common/               # 基础设施
│   │   │   ├── base_model.py     # 抽象基类（时间戳 + 软删除）
│   │   │   ├── managers.py       # BaseManager（自动过滤已删除记录）
│   │   │   └── exceptions.py     # BusinessError + DRF 统一错误处理器
│   │   ├── rbac/                 # 用户与权限
│   │   │   ├── models.py         # User / Role (含 is_unique ) / UserRole / RolePermission
│   │   │   ├── backends.py       # 自定义认证后端 UserBackend（过滤软删除）
│   │   │   ├── services/         # 业务逻辑层
│   │   │   │   ├── user_service.py      # 用户注册/更新/角色分配
│   │   │   │   └── role_service.py      # 角色 CRUD + BOSS 唯一性校验
│   │   │   ├── serializers/      # 输入输出序列化器
│   │   │   │   ├── user_serializers.py
│   │   │   │   └── role_serializers.py
│   │   │   ├── views/            # HTTP 接口层
│   │   │   │   ├── auth_views.py        # 登录/登出（响应返回角色列表）
│   │   │   │   ├── user_views.py        # 用户 CRUD（IsAdminOrReadOnly）
│   │   │   │   ├── role_views.py        # 角色 CRUD（IsAdminOrReadOnly）
│   │   │   │   └── dashboard_views.py   # Dashboard 实时统计
│   │   │   ├── urls_auth.py      # 认证路由
│   │   │   ├── urls_user.py      # 用户管理路由
│   │   │   ├── urls_role.py      # 角色管理路由
│   │   │   ├── urls_dashboard.py # 仪表盘路由
│   │   │   └── management/commands/init_rbac.py  # 初始化角色 + admin
│   │   └── audit/                # 审计（预留）
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── vite.config.ts            # Vite 配置（代理 /api → 后端）
│   └── src/
│       ├── main.ts               # 入口
│       ├── App.vue               # 根组件
│       ├── router/index.ts       # 路由表 + 导航守卫
│       ├── stores/user.ts        # Vuex 认证模块
│       ├── api/
│       │   ├── client.ts         # Axios 实例（拦截器统一错误处理）
│       │   └── modules/          # 按模块拆分 API
│       ├── types/
│       │   ├── user.ts          # TS 类型契约
│       │   └── role.ts          # 角色类型契约
│       ├── layouts/MainLayout.vue  # 含角色管理导航
│       └── views/
│           ├── login/
│           ├── dashboard/
│           │   └── DashboardView.vue  # 实时统计仪表盘
│           ├── error/
│           └── system/
│               ├── user/         # 用户管理（含角色选择器）
│               │   ├── UserListView.vue
│               │   └── UserFormDialog.vue
│               └── role/         # 角色管理
│                   ├── RoleListView.vue
│                   └── RoleFormDialog.vue
│
├── docs/                         # 设计文档
├── changelog/                    # 更新日志
│   ├── CHANGELOG.md              # 更新索引
│   ├── CONFIG.md                 # 配置清单（端口/环境变量/生产部署）
│   └── 2026-06-09_*.md           # 各版本详细记录
├── ARCHITECTURE.md               # 架构详解（给新人）
└── README.md
```

---

## 快速开始

### 环境要求

- **Python** 3.13+
- **Node.js** 22+

### 1. 克隆项目

```bash
git clone <repo-url>
cd ram-adminx
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活（Windows）
venv\Scripts\activate

# 激活（macOS / Linux）
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 初始化管理员
python manage.py init_rbac

# 启动服务
python manage.py runserver
```

后端运行在 `http://127.0.0.1:8000`

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在 `http://localhost:5173`

### 4. 登录

打开浏览器访问 `http://localhost:5173/login`

| 用户名 | 密码 |
|--------|------|
| `admin` | `admin123` | root（超级管理员） |

> `init_rbac` 命令同时创建 boss001/boss123 和 user001/user123 测试账号。

---

## API 文档

### 认证

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/auth/csrf/` | 获取 CSRF Token |
| POST | `/api/auth/login/` | 登录 |
| POST | `/api/auth/logout/` | 登出 |
| GET | `/api/auth/user-info/` | 当前用户信息 |

### 用户管理（需登录）

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/rbac/users/` | 列表（`?search=&page=&page_size=`） |
| POST | `/api/rbac/users/` | 创建用户 |
| GET | `/api/rbac/users/{id}/` | 详情 |
| PUT | `/api/rbac/users/{id}/` | 更新 |
| DELETE | `/api/rbac/users/{id}/` | 软删除 |
| POST | `/api/rbac/users/{id}/reset-password/` | 重置密码 |

### 角色管理（需管理员登录）

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/rbac/roles/` | 角色列表 |
| POST | `/api/rbac/roles/` | 创建角色（BOSS 全局唯一） |
| GET | `/api/rbac/roles/{id}/` | 角色详情 |
| PUT | `/api/rbac/roles/{id}/` | 更新角色 |
| DELETE | `/api/rbac/roles/{id}/` | 删除角色（系统角色不可删） |

### 仪表盘（需登录）

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/dashboard/stats/` | 实时统计数据（用户数/活跃数/角色数/分配数） |

### 响应格式

**成功**:
```json
{
  "data": { ... },
  "pagination": { "page": 1, "page_size": 20, "total": 42, "total_pages": 3 }
}
```

**错误**:
```json
{
  "error": {
    "code": "DUPLICATE_USERNAME",
    "message": "用户名已存在"
  }
}
```

---

## 架构说明

项目采用严格分层架构：

```
ViewSet (HTTP 接口) → Service (业务逻辑) → Manager (查询封装) → Model (表结构)
   ↕
Serializer (数据转换 / 输入校检)
```

- **ViewSet** — 只处理 HTTP 相关（参数解析、响应包装），不写业务逻辑
- **Service** — 纯业务代码，使用 `@transaction.atomic` 保证事务，`BusinessError` 抛异常
- **Manager** — `BaseManager` 自动过滤 `is_deleted=True` 的记录（软删除透明化）
- **Serializer** — Create / Update / Output 三类严格分离，防止字段泄露
- **前端** — 路由守卫做登录拦截，Axios 拦截器统一处理 401/403
- **权限** — 后端 `IsAdminOrReadOnly` 权限类：普通用户只读，root/BOSS 可写；前端 `isAdmin` getter 控制按钮显隐

详见 [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## 开发命令

```bash
# 后端
python manage.py runserver           # 启动 Django
python manage.py makemigrations      # 生成迁移
python manage.py migrate             # 执行迁移
python manage.py init_rbac           # 初始化 RBAC 数据

# 前端
npm run dev                          # 启动 Vite
npm run build                        # 生产构建（vue-tsc + vite）
npm run lint                         # ESLint 检查
```

---

## 安全设计

| 机制 | 说明 |
|------|------|
| 密码存储 | bcrypt 哈希（`make_password`） |
| 认证 | Session Cookie（HttpOnly + SameSite=Lax） |
| 防跨站 | CSRF Token（Cookie + Header 双重校验） |
| 软删除 | `is_deleted` 字段 + `BaseManager` 自动过滤 |
| 事务 | `@transaction.atomic` 保证写操作原子性 |
| 输入校验 | Serializer 字段级规则 |
| 输出过滤 | 只暴露声明的字段，密码字段不可见 |
| 访问控制 | `IsAdminOrReadOnly` — 普通用户只读，管理员可写 |
| BOSS 唯一 | 数据库 + Service 双层校验，全局唯一管理员账号 |
