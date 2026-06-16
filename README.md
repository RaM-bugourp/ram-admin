# Ram-AdminX

> Django 5.2 + Vue 3 + Arco Design 现代化后台管理系统（含 AI 智能模块）

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green)](https://djangoproject.com)
[![Vue](https://img.shields.io/badge/Vue-3.5-brightgreen)](https://vuejs.org)
[![Arco Design](https://img.shields.io/badge/Arco_Design-2.56-165dff)](https://arco.design/vue)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 当前版本

**v1.0.2** — 操作审计日志 + 登录流程 Bug 修复 + 前端构建稳定性

### v1.0.2 新增

- **审计日志模块** — 记录登录登出、用户管理、角色管理的全部操作，含 IP / UA / 详情 / 扩展数据
- **审计统计** — 总日志数 / 今日操作 / 今日登录 / 按操作类型和资源类型聚合
- **审计前端页面** — 统计卡片 + 多维过滤（日志类型/资源类型/用户名/日期范围）+ 分页表格 + 清理弹窗
- **登录流程修复** — 修复 `await` 缺失导致 store 状态未就绪时路由守卫拦截跳转的问题
- **表单提交修复** — `ev.preventDefault()` 防止浏览器原生提交刷新页面
- **401 递归防护** — Axios 拦截器加互斥锁，防止 `isLoggingOut` 状态下的无限重定向
- **TypeScript 构建修复** — 修复 4 个类型错误（Icon 改名 / 缺少 `:model` / 接口名冲突），生产构建零错误通过

### v0.4.0 功能（AI 模块）

- **AI 对话** — 自然语言交互，多 Provider 自动故障转移（OpenAI → DeepSeek → QClaw）
- **数据分析** — 自然语言查询数据、智能洞察生成、自动报告生成
- **Agent 审批** — 两阶段审批工作流，Agent 写操作必须 root 审批后执行
- **全链路审计** — 谁调用 / 调了哪个 Provider / 是否故障转移 / Agent 操作谁审批
- **Root 告警** — Provider 故障时自动通知所有 root 账户（站内通知 + 可选 Webhook）
- **Agent Token** — HMAC-SHA256 无状态 Token 签发与验证，支持 Agent 授权调用
- **数据脱敏** — 递归清除敏感字段，防止 AI Prompt 泄露用户隐私
- **Mock 模式** — 未配置 API Key 时自动启用本地占位回复，方便开发调试

### v0.3.0 功能（RBAC 核心）

- **认证系统** — 自定义 User 模型（`AbstractBaseUser`）、Session + CSRF 双重保护
- **用户管理** — 列表分页搜索、创建/编辑/删除（软删除）、密码重置、多角色分配
- **角色管理** — 三级角色体系 (root/BOSS/user)，CRUD 完整支持，BOSS 全局唯一校验
- **权限控制** — `IsAdminOrReadOnly` 后端权限类 + 前端按钮按角色显隐（`isAdmin` getter）
- **仪表盘** — 实时统计（用户数/活跃用户/角色数/角色分配数）
- **分层架构** — ViewSet → Service → Manager → Model 四层解耦

### 规划中

- 菜单管理 & 动态路由
- 权限粒度分配（按钮级）
- 操作日志  ✅ **（v1.0.2 已完成）**
- 代码生成器
- 流式响应（AI 对话 SSE）
- Token 计数 & 费用统计

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Django 5.2 + Django REST Framework 3.15 |
| 数据库 | SQLite（开发）→ PostgreSQL（生产） |
| 前端框架 | Vue 3.5 (Composition API) + TypeScript 5.5 |
| UI 组件库 | Arco Design Vue 2.56 |
| 状态管理 | Vuex 4 |
| 路由 | Vue Router 4 |
| HTTP 客户端 | Axios（withCredentials + CSRF） |
| 构建工具 | Vite 6 |
| AI 集成 | 多 Provider（OpenAI / DeepSeek / QClaw），故障转移 + 熔断器 |

---

## 项目结构

```
ram-adminx/
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py           # 公共配置（中间件、DRF、认证模型、AI Provider 配置）
│   │   │   └── dev.py            # 开发环境覆盖
│   │   └── urls.py               # 根路由（auth / rbac / dashboard / ai）
│   ├── apps/
│   │   ├── common/               # 基础设施
│   │   │   ├── base_model.py     # 抽象基类（时间戳 + 软删除）
│   │   │   ├── managers.py       # BaseManager（自动过滤已删除记录）
│   │   │   └── exceptions.py     # BusinessError + DRF 统一错误处理器
│   │   ├── rbac/                 # 用户与权限
│   │   │   ├── models.py         # User / Role / UserRole / RolePermission
│   │   │   ├── backends.py       # 自定义认证后端（过滤软删除）
│   │   │   ├── permissions.py    # IsAdminOrReadOnly 权限类
│   │   │   ├── services/         # 业务逻辑层（user_service / role_service）
│   │   │   ├── serializers/      # 输入输出序列化器
│   │   │   ├── views/            # HTTP 接口层（auth / user / role / dashboard）
│   │   │   ├── urls_*.py         # 路由拆分
│   │   │   └── management/commands/init_rbac.py  # 初始化角色 + admin
│   │   ├── audit/                # 操作审计
│   │   │   ├── models.py         # AuditLog（登录/登出/CRUD 全链路追踪）
│   │   │   ├── utils.py          # log_audit() 埋点工具
│   │   │   ├── serializers.py    # AuditLogSerializer / 统计序列化器
│   │   │   ├── views.py          # AuditLogViewSet（列表/统计/清理/枚举）
│   │   │   └── urls.py           # Router 注册
│   │   └── ai/                   # AI 智能模块
│   │       ├── models.py         # AICallLog / AIApproval / AIApprovalLog / Notification
│   │       ├── permissions.py    # RootOnlyAI / RootOrAgentAuth / AgentTokenService
│   │       ├── services/
│   │       │   ├── ai_service.py       # 核心 AI 服务（故障转移 + 频次限制）
│   │       │   ├── ai_client.py       # HTTP 客户端（OpenAI 兼容协议）
│   │       │   ├── ai_failover.py      # 熔断器 + Provider 状态机
│   │       │   ├── ai_approval.py      # 两阶段审批工作流
│   │       │   ├── ai_audit.py         # 审计日志记录
│   │       │   ├── ai_errors.py        # AI 异常体系
│   │       │   ├── prompt_builder.py   # Prompt 工程
│   │       │   ├── data_formatter.py   # 数据脱敏
│   │       │   ├── notification_service.py # 站内通知 + Webhook 告警
│   │       │   └── stats_service.py    # 统计数据采集
│   │       ├── views/            # chat / analyze / report / approval / audit / notification / agent-token
│   │       ├── serializers/      # 14 个 Serializer 覆盖全部输入输出
│   │       ├── urls.py           # DefaultRouter 注册全部 ViewSet
│   │       └── management/commands/  # ai_status / cleanup_ai_audit
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── vite.config.ts            # Vite 配置（代理 /api → 后端）
│   └── src/
│       ├── main.ts               # 入口
│       ├── App.vue               # 根组件
│       ├── router/index.ts       # 路由表 + 导航守卫（含 root 权限检查）
│       ├── stores/
│       │   ├── user.ts           # 用户/认证状态
│       │   └── ai.ts             # AI 模块状态（Provider 状态、通知未读）
│       ├── api/
│       │   ├── client.ts         # Axios 实例（拦截器统一错误处理）
│       │   └── modules/          # 按模块拆分 API（auth / user / role / dashboard / ai）
│       ├── types/                # TypeScript 类型定义（user / role / ai）
│       ├── utils/
│       │   └── markdown.ts       # 极简 Markdown 渲染器（XSS 安全）
│       ├── components/
│       │   └── AIProviderAlert.vue  # AI Provider 状态告警横幅
│       ├── layouts/MainLayout.vue   # 主布局（侧边栏 AI 菜单组、待审批/未读角标）
│       └── views/
│           ├── login/            # 登录页
│           ├── dashboard/        # 仪表盘
│           ├── error/            # 403 / 404
│           ├── system/            # 用户管理 / 角色管理
│           └── ai/               # AI 对话 / Agent 审批 / AI 审计 / AI 通知 / Agent Token
│
├── docs/                         # 设计文档（后端 15 篇 + 前端 5 篇 + DevOps 2 篇）
├── changelog/                    # 更新日志
│   ├── CHANGELOG.md              # 更新索引
│   ├── CONFIG.md                 # 配置清单（端口/环境变量/生产部署）
│   └── 2026-06-*.md              # 各版本详细记录
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

| 用户名 | 密码 | 角色 |
|--------|------|------|
| `admin` | `admin123` | root（超级管理员） |
| `boss001` | `boss123` | BOSS（全局唯一管理员） |
| `user001` | `user123` | user（普通用户） |

> AI 功能仅对 `root` 角色可见，使用 `admin` 账号登录即可体验全部功能。

---

## AI 模块配置

AI 模块支持多 Provider 故障转移。通过环境变量配置：

```bash
# Provider 1 — OpenAI（主力）
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4o-mini"

# Provider 2 — DeepSeek（备用）
export DEEPSEEK_API_KEY="sk-..."
export DEEPSEEK_MODEL="deepseek-chat"

# Provider 3 — QClaw（兜底）
export QCLAW_API_KEY="sk-..."
export QCLAW_MODEL="pool-deepseek-v4-pro"

# 故障转移参数（可选，有默认值）
export AI_FAILOVER_FAILURE_THRESHOLD=3    # 连续失败次数触发熔断
export AI_FAILOVER_RECOVERY_TIMEOUT=60     # 熔断恢复超时（秒）
export AI_MOCK_WHEN_NO_KEY=false           # 关闭 Mock 模式（未配 Key 时报错）
```

> 未配置任何 API Key 时，默认启用 Mock 模式返回本地占位回复，方便开发调试。

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
| GET | `/api/dashboard/stats/` | 实时统计数据 |

### 审计日志（需管理员登录）

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/audit/logs/` | 审计日志列表（支持 action/resource/username/日期范围过滤） |
| GET | `/api/audit/logs/stats/` | 审计统计（总量/按操作/按资源/今日数据） |
| GET | `/api/audit/logs/actions/` | 操作类型枚举选项 |
| GET | `/api/audit/logs/resources/` | 资源类型枚举选项 |
| DELETE | `/api/audit/logs/cleanup/?days=90` | 清理过期日志 |

### AI 模块（仅 root）

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/ai/chat/chat/` | AI 对话 |
| GET | `/api/ai/chat/provider-status/` | Provider 池状态 |
| POST | `/api/ai/analyze/analyze/` | 自然语言数据分析 |
| GET | `/api/ai/analyze/insights/` | 仪表盘智能洞察 |
| POST | `/api/ai/report/report/` | 自动报告生成 |
| POST | `/api/ai/approval/submit/` | 提交审批 |
| GET | `/api/ai/approval/` | 审批列表 |
| GET | `/api/ai/approval/{id}/` | 审批详情 |
| POST | `/api/ai/approval/{id}/review/` | 审批（approve/reject） |
| GET | `/api/ai/audit/` | 审计日志列表 |
| GET | `/api/ai/audit/summary/` | 审计统计摘要 |
| GET | `/api/ai/notifications/` | 通知列表 |
| POST | `/api/ai/notifications/{id}/read/` | 标记已读 |
| POST | `/api/ai/notifications/read-all/` | 全部标记已读 |
| POST | `/api/ai/agent-token/issue/` | 签发 Agent Token |

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
- **前端** — 路由守卫做登录拦截 + root 权限检查，Axios 拦截器统一处理 401/403
- **权限** — 后端 `IsAdminOrReadOnly` 权限类；AI 模块使用 `RootOnlyAI` / `RootOrAgentAuth`
- **AI 架构** — 多 Provider N+1 故障转移，CircuitBreaker 熔断器（HEALTHY → FAILED → DEGRADED）

详见 [`ARCHITECTURE.md`](ARCHITECTURE.md)

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
| AI 权限 | `RootOnlyAI` — AI 功能仅 root 可用 |
| Agent Token | HMAC-SHA256 签名 + 过期检查，无状态验证 |
| 数据脱敏 | AI Prompt 发送前递归清除敏感字段（密码/邮箱/手机号等 14 项） |
| 频次限制 | Root 用户 100 次/小时，Agent 20 次/小时 |
| 操作审计 | 全链路审计日志 — 登录/CRUD/权限变更全记录，IP + UA 可追溯 |

---

## 开发命令

```bash
# ── 后端 ─────────────────────────────────
python manage.py runserver           # 启动 Django
python manage.py makemigrations      # 生成迁移
python manage.py migrate             # 执行迁移
python manage.py init_rbac           # 初始化 RBAC 数据

# AI 管理命令
python manage.py ai_status            # 查看 AI Provider 状态
python manage.py cleanup_ai_audit    # 清理过期审计日志

# ── 前端 ─────────────────────────────────
npm run dev                          # 启动 Vite
npm run build                        # 生产构建（vue-tsc + vite）
npm run lint                         # ESLint 检查
```

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 项目架构详解（新人必读） |
| [docs/ai-integration-design.md](docs/ai-integration-design.md) | AI 集成设计文档 |
| [changelog/CHANGELOG.md](changelog/CHANGELOG.md) | 版本更新日志 |
| [changelog/CONFIG.md](changelog/CONFIG.md) | 环境配置清单 |
| [docs/backend/](docs/backend/) | 后端开发文档（15 篇） |
| [docs/frontend/](docs/frontend/) | 前端开发文档（5 篇） |
| [docs/devops/](docs/devops/) | DevOps 文档（部署/监控） |

---

## License

MIT
