# Ram-AdminX

> Django 5.2 + Vue 3 + Arco Design 现代化后台管理系统（含 AI 智能模块）

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green)](https://djangoproject.com)
[![Vue](https://img.shields.io/badge/Vue-3.5-brightgreen)](https://vuejs.org)
[![Arco Design](https://img.shields.io/badge/Arco_Design-2.56-165dff)](https://arco.design/vue)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF)](https://vitejs.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 项目状态

**版本 v0.4.0 | 成熟度: BETA — 核心功能就绪，适合中小团队使用**

| 维度 | 评分 | 说明 |
|------|------|------|
| 核心功能 | ⭐⭐⭐⭐⭐ | RBAC + 用户角色管理 + AI 模块完整可用 |
| 架构设计 | ⭐⭐⭐⭐⭐ | ViewSet→Service→Manager→Model 四层解耦，模块化程度高 |
| 安全性 | ⭐⭐⭐⭐ | Session+CSRF+bcrypt+软删除+脱敏，基础安全到位 |
| 文档完善度 | ⭐⭐⭐⭐⭐ | 架构文档 + 22 篇设计文档 + 更新日志 + 配置清单 |
| 前端体验 | ⭐⭐⭐⭐ | Arco Design UI 美观，TypeScript 全覆盖 |
| 测试覆盖 | ⚪ | **缺失** — 无单元/集成测试 |
| 运维成熟度 | ⭐⭐ | 缺少 CI/CD、Docker、容器化部署 |

---

## 当前版本

**v0.4.0** — AI 智能模块集成 + N+1 故障转移 + Agent 审批流 + 全链路审计

### v0.4.0 新增（AI 模块）

- **AI 对话** — 自然语言交互，多 Provider 自动故障转移（OpenAI → DeepSeek → QClaw）
- **Circuit Breaker 熔断器** — 3 种状态（HEALTHY / FAILED / DEGRADED），自动恢复
- **Agent 审批工作流** — 两阶段审批，Agent 写操作必须 root 审批后执行
- **Agent Token 鉴权** — HMAC-SHA256 无状态 Token 签发与验证（`<exp>.<uid>.<agent_id>.<sig>`）
- **全链路审计** — 谁调用 / 调了哪个 Provider / 是否故障转移 / 谁审批了什么操作
- **站内通知系统** — Provider 故障自动通知所有 root 账户 + 可选 Webhook（钉钉/企微）
- **数据脱敏** — 递归清除 14 项敏感字段，深拷贝保护，防止 AI Prompt 泄露隐私
- **频次限制** — Root 用户 100 次/小时，Agent 20 次/小时
- **Mock 模式** — 未配置 API Key 时自动启用本地占位回复
- **审计摘要** — 多维度统计数据汇总
- **清理命令** — `cleanup_ai_audit` 管理命令（默认 90 天保留期）

### v0.3.0 功能（RBAC 核心）

- **认证系统** — 自定义 User 模型（`AbstractBaseUser`）、Session + CSRF（HTTP-Only + SameSite=Lax）
- **用户管理** — 列表分页搜索、创建/编辑/软删除、密码重置、多角色分配
- **角色管理** — 三级角色体系（root/BOSS/user），BOSS 全局唯一（DB + Service 双层校验）
- **权限控制** — `IsAdminOrReadOnly` 后端权限类 + 前端按钮按角色显隐（`isAdmin`/`isRoot` getter）
- **仪表盘** — 实时统计数据（用户总数 / 活跃用户 / 角色数 / 角色分配数）
- **分层架构** — ViewSet → Service → Manager → Model 四层解耦

### 规划中

- 菜单管理与动态路由（已有设计文档）
- 按钮级权限分配
- 操作日志系统
- 代码生成器
- 流式响应（AI 对话 SSE）
- Token 计数与费用统计
- 国际化（i18n，已有设计文档）
- 文件管理与存储（已有设计文档）
- 数据导出与报表（已有设计文档）
- 完整错误码体系（已有设计文档）
- 数据权限（已有设计文档）
- 可观测性与监控告警（已有设计文档）
- **单元/集成测试** ⚠️

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Django 5.2 + Django REST Framework 3.15 |
| 数据库 | SQLite（开发）→ PostgreSQL（生产） |
| 前端框架 | Vue 3.5 (Composition API) + TypeScript 5.5 |
| UI 组件库 | Arco Design Vue 2.56 |
| 状态管理 | Vuex 4 |
| 路由 | Vue Router 4（登录守卫 + root 权限守卫） |
| HTTP 客户端 | Axios（withCredentials + CSRF 双重校验） |
| 构建工具 | Vite 6 |
| AI 集成 | 多 Provider（OpenAI / DeepSeek / QClaw），故障转移 + 熔断器 + 频次限制 |

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
│   │   │   ├── backends.py       # 自定义认证后端（过滤软删除用户）
│   │   │   ├── permissions.py    # IsAdminOrReadOnly 权限类
│   │   │   ├── services/         # 业务逻辑层（user_service / role_service）
│   │   │   ├── serializers/      # 输入输出序列化器（Create/Update/Output 分离）
│   │   │   ├── views/            # HTTP 接口层（auth / user / role / dashboard）
│   │   │   └── management/commands/init_rbac.py  # 初始化角色 + admin
│   │   ├── audit/                # 审计模块（预留）
│   │   └── ai/                   # AI 智能模块
│   │       ├── models.py         # AICallLog / AIApproval / AIApprovalLog / Notification
│   │       ├── permissions.py    # RootOnlyAI / RootOrAgentAuth / AgentTokenService
│   │       ├── services/
│   │       │   ├── ai_service.py        # 核心 AI 服务（故障转移 + 频次限制）
│   │       │   ├── ai_client.py         # HTTP 客户端（OpenAI 兼容协议）
│   │       │   ├── ai_failover.py       # 熔断器 + Provider 状态机（线程安全）
│   │       │   ├── ai_approval.py       # 两阶段审批工作流
│   │       │   ├── ai_audit.py          # 审计日志记录
│   │       │   ├── ai_errors.py         # AI 异常体系
│   │       │   ├── prompt_builder.py    # Prompt 工程
│   │       │   ├── data_formatter.py    # 数据脱敏（递归清除敏感字段）
│   │       │   ├── notification_service.py  # 站内通知 + Webhook 告警
│   │       │   └── stats_service.py     # 统计数据采集
│   │       ├── views/             # chat / analyze / report / approval / audit / notification / agent-token
│   │       ├── serializers/       # 14 个 Serializer 覆盖全部输入输出
│   │       ├── urls.py            # DefaultRouter 注册全部 ViewSet
│   │       └── management/commands/  # ai_status / cleanup_ai_audit
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── vite.config.ts            # Vite 配置（代理 /api → 后端 :8000）
│   └── src/
│       ├── main.ts               # 入口（createApp + 插件注册）
│       ├── App.vue               # 根组件
│       ├── router/index.ts       # 路由表 + 导航守卫（登录拦截 + requireRoot 检查）
│       ├── stores/
│       │   ├── index.ts          # Vuex Store 实例
│       │   ├── user.ts           # 用户/认证状态 + isAdmin/isRoot getter
│       │   └── ai.ts             # AI 模块状态（Provider 状态、通知未读数）
│       ├── api/
│       │   ├── client.ts         # Axios 实例 + 拦截器（统一错误处理）
│       │   └── modules/          # 按模块拆分（auth / user / role / dashboard / ai）
│       ├── types/                # TypeScript 类型契约（user / role / ai，20+ 接口）
│       ├── utils/
│       │   └── markdown.ts       # 极简 Markdown 渲染器（XSS 安全）
│       ├── components/
│       │   └── AIProviderAlert.vue  # AI Provider 状态告警横幅
│       ├── layouts/MainLayout.vue   # 主布局（侧边栏 AI 菜单组、待审批/未读角标）
│       └── views/
│           ├── login/            # LoginView — 登录页
│           ├── dashboard/        # DashboardView — 4 个统计卡片
│           ├── error/            # 403 Forbidden / 404 Not Found
│           ├── system/           # 用户管理 / 角色管理
│           └── ai/               # AI 对话 / Agent 审批 / AI 审计 / AI 通知 / Agent Token
│
├── docs/                         # 设计文档集（23 篇）
│   ├── backend/                  # 后端 15 篇（Model/Service/Serializer/ViewSet/安全/审计/国际化…）
│   ├── frontend/                 # 前端 5 篇（基础架构/API层/页面组件/安全优化/动态路由）
│   └── devops/                   # DevOps 2 篇（部署CI-CD/可观测性）
├── changelog/                    # 版本更新日志 + 配置清单
│   ├── CHANGELOG.md
│   └── CONFIG.md
├── ARCHITECTURE.md               # 架构详解（新人必读）
└── README.md
```

---

## 架构设计

### 后端四层架构

```
ViewSet (HTTP 接口)  →  只处理 HTTP（参数解析、响应包装），不写业务逻辑
   ↓
Service (业务逻辑)   →  @transaction.atomic 保证事务，BusinessError 抛异常
   ↓
Manager (查询封装)   →  BaseManager 自动过滤 is_deleted=True（软删除透明化）
   ↓
Model (表结构)       →  6 张业务表 + 1 张 Django 系统表
   ↕
Serializer (数据转换) →  Create/Update/Output 三类严格分离，防止字段泄露
```

### 前端架构

```
Vue Router (登录守卫 + requireRoot) → Page View → Axios Client (withCredentials + CSRF)
                                          ↕
                                    Vuex Store (user / ai)
                                          ↕
                                    TypeScript 类型契约 (types/*.ts)
```

### 架构亮点

- **接口化设计** — 各层职责清晰，Service 不关心 HTTP，ViewSet 不写业务逻辑
- **惰性导入** — 函数内部 import，避免启动时因缺少依赖崩溃
- **结果对象模式** — 返回结果对象而非 None，包含 error 字段，调用方易处理
- **状态管理** — CircuitBreaker 线程安全单例，支持并发调用下的熔断状态一致
- **异常体系** — BusinessError → custom_exception_handler → 统一 JSON 格式
- **软删除透明化** — BaseManager 自动过滤已删除记录，`with_deleted()` 按需查询

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

| 用户名 | 密码 | 角色 |
|--------|------|------|
| `admin` | `admin123` | root（超级管理员） |
| `boss001` | `boss123` | BOSS（全局唯一管理员） |
| `user001` | `user123` | user（普通用户） |

> AI 功能仅对 `root` 角色可见，使用 `admin` 账号登录即可体验全部功能。

---

## AI 模块配置

AI 模块支持多 Provider 故障转移，通过 settings 或环境变量配置：

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
export AI_FAILOVER_RECOVERY_TIMEOUT=60    # 熔断恢复超时（秒）
export AI_MOCK_WHEN_NO_KEY=false          # 关闭 Mock 模式（未配 Key 时报错）
```

> 未配置任何 API Key 时，默认启用 Mock 模式返回本地占位回复，方便开发调试。

---

## API 文档

### 认证

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/auth/csrf/` | 获取 CSRF Token |
| POST | `/api/auth/login/` | 登录（返回角色列表） |
| POST | `/api/auth/logout/` | 登出 |
| GET | `/api/auth/user-info/` | 当前用户信息与角色列表 |

### 用户管理（需登录）

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/rbac/users/` | 列表（支持 `?search=&page=&page_size=`） |
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
| GET | `/api/dashboard/stats/` | 实时统计（用户数/活跃用户/角色数/分配数） |

### AI 模块（仅 root）

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/ai/chat/chat/` | AI 对话 |
| GET | `/api/ai/chat/provider-status/` | Provider 池状态 |
| POST | `/api/ai/analyze/analyze/` | 自然语言数据分析 |
| GET | `/api/ai/analyze/insights/` | 仪表盘智能洞察 |
| POST | `/api/ai/report/report/` | 自动报告生成 |
| POST | `/api/ai/approval/submit/` | Agent 提交审批 |
| GET | `/api/ai/approval/` | 审批列表（支持按状态过滤） |
| GET | `/api/ai/approval/{id}/` | 审批详情 |
| POST | `/api/ai/approval/{id}/review/` | 审批（approve/reject） |
| GET | `/api/ai/audit/` | 审计日志列表（按日期/类型/用户/Agent 筛选） |
| GET | `/api/ai/audit/summary/` | 审计统计摘要 |
| GET | `/api/ai/notifications/` | 通知列表 |
| POST | `/api/ai/notifications/{id}/read/` | 标记已读 |
| POST | `/api/ai/notifications/read-all/` | 全部标记已读 |
| POST | `/api/ai/agent-token/issue/` | 签发 Agent Token（HMAC-SHA256） |

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

## 安全设计

| 机制 | 说明 |
|------|------|
| 密码存储 | bcrypt 哈希（`make_password`） |
| 认证 | Session Cookie（HttpOnly + SameSite=Lax） |
| 防跨站 | CSRF Token（Cookie + Header 双重校验） |
| 软删除 | `is_deleted` 字段 + `BaseManager` 自动过滤 |
| 事务 | `@transaction.atomic` 保证写操作原子性 |
| 输入校验 | Serializer 字段级规则 |
| 输出过滤 | Create / Update / Output Serializer 严格分离 |
| 访问控制 | `IsAdminOrReadOnly` — 普通用户只读，管理员可写 |
| BOSS 唯一 | 数据库 + Service 双层校验，全局唯一管理员 |
| AI 权限 | `RootOnlyAI` — AI 功能仅 root 可用 |
| Agent Token | HMAC-SHA256 签名 + 过期检查，无状态验证 |
| 数据脱敏 | AI 调用前递归清除 14 项敏感字段，深拷贝不污染原始数据 |
| 频次限制 | Root 100 次/小时，Agent 20 次/小时 |
| 熔断保护 | CircuitBreaker（HEALTHY → FAILED → DEGRADED） |
| Mock 模式 | 未配置 Key 时本地占位，避免暴露未授权信息 |

---

## 开发命令

```bash
# ── 后端 ─────────────────────────────────
python manage.py runserver                 # 启动 Django
python manage.py makemigrations             # 生成迁移
python manage.py migrate                    # 执行迁移
python manage.py init_rbac                  # 初始化 RBAC 数据

# AI 管理命令
python manage.py ai_status                  # 查看 AI Provider 状态
python manage.py cleanup_ai_audit           # 清理过期审计日志（默认 90 天）

# ── 前端 ─────────────────────────────────
npm run dev                                 # 启动 Vite 开发服务器
npm run build                               # 生产构建（vue-tsc + vite）
npm run lint                                # ESLint 检查
```

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 项目架构详解（新人必读） |
| [docs/ai-integration-design.md](docs/ai-integration-design.md) | AI 集成设计文档 |
| [changelog/CHANGELOG.md](changelog/CHANGELOG.md) | 版本更新日志 |
| [changelog/CONFIG.md](changelog/CONFIG.md) | 环境配置清单 |
| [docs/backend/](docs/backend/) | 后端开发文档（15 篇，覆盖全部开发阶段） |
| [docs/frontend/](docs/frontend/) | 前端开发文档（5 篇） |
| [docs/devops/](docs/devops/) | DevOps 文档（部署/CI-CD/监控） |

**后端文档索引（15 篇）**:
01. 项目初始化与配置 | 02. Model 层开发 | 03. Repository 层开发 | 04. Service 层开发
05. Serializer 契约层 | 06. ViewSet 接口层 | 07. 权限与安全 | 08. 中间件开发
09. 审计与日志 | 10. 测试开发 | 11. 代码生成器 | 17. 文件管理与存储
19. 数据导出与报表 | 20. 错误码体系 | 21. 数据权限设计 | 22. 国际化方案

**前端文档索引（5 篇）**:
12. 前端基础架构 | 13. 前端 API 层与类型 | 14. 前端页面组件开发
15. 前端安全与优化 | 18. 动态路由与菜单管理

**DevOps 文档索引（2 篇）**:
16. 部署与 CI-CD | 23. 可观测性与监控

---

## License

MIT
