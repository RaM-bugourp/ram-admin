# Ram-AdminX

基于 Django、Vue 3 与 Arco Design Vue 的通用管理后台，提供用户与角色管理、会话安全、操作审计，以及可选的 AI 辅助功能。

**当前版本：0.3.0-dev.1（开发预发行）**。本版本重点补充账户安全中心、审计 CSV 导出和本机 SQLite 备份/隔离恢复工具。尚未完成生产部署与安全总审，不应将开发验证视为生产就绪承诺。

## 功能

- **用户与 RBAC**：用户分页查询、创建、编辑、软删除、密码重置与多角色分配；支持 root、BOSS、普通用户及自定义角色。核心权限为 `dashboard.read`、`users.read`、`users.write`、`roles.read`、`roles.write`、`audit.read`；后端逐请求检查有效身份与当前权限，并限制越权分配和管理员接管。
- **账户安全中心**：Session 认证与 CSRF 校验；持久登录限速按账号和来源分别计数，300 秒窗口内限额分别为 8 和 40 次，返回 429 与 `Retry-After`，容量不足时拒绝服务。来源仅取 `REMOTE_ADDR`，不信任 `X-Forwarded-For`。本人可查看会话、撤销单个会话、退出其他会话；root 可撤销目标用户全部会话。会话句柄为独立 UUID，不暴露 Session Key。
- **操作审计**：核心操作与安全事件记录、分页列表和严格筛选；CSV 与列表共用筛选逻辑，UTF-8 BOM、固定字段、控制字符清洗与公式前缀中和。导出超过 5000 行时拒绝并要求收窄条件，不静默截断。
- **工作台与个人设置**：用户/角色等统计、个人信息、修改密码与会话管理。
- **可选 AI**：对话、分析、报告、Agent 审批、Token 签发与撤销；支持 OpenAI 兼容 Provider、故障转移与熔断。默认隐藏 AI 界面，核心管理功能不依赖外部模型服务。
- **本机 SQLite 运维**：健康检查、SQLite 在线一致性备份、独立目录恢复及完整性校验，不覆盖正在使用的数据库。

## 技术栈与环境

| 部分 | 当前依赖/配置 |
| --- | --- |
| 后端 | Django `>=5.2,<5.3`、Django REST Framework `>=3.15`、django-cors-headers `>=4.6`、django-filter `>=24.1` |
| 数据库 | SQLite；当前开发配置和 production 配置均使用 SQLite |
| 前端 | Vue 3.5、TypeScript、Arco Design Vue 2.x、Vue Router 4、Vuex 4、Axios |
| 构建 | Vite 6、vue-tsc；使用 npm 锁文件安装 |

后端依赖见 [requirements.txt](backend/requirements.txt)，其中没有独立声明 Python 最低版本；Django 5.2 要求 Python 3.10 及以上，其他未锁定上限的依赖还可能提高要求，安装时需核对解析结果。建议为本项目使用独立 Python 3.11 或更新的兼容环境。前端建议使用 Node.js 22 LTS 与随附 npm；锁文件中的 Vite 6 声明支持 Node.js 18、20 或 22 及以上兼容版本，不应将旧徽章当作环境要求。精确依赖以 [package.json](frontend/package.json) 与 [package-lock.json](frontend/package-lock.json) 为准。

## 快速开始

以下命令用于全新本地开发副本。不要复制旧版本的数据库、环境文件或演示账号；已有部署升级前应另做备份与迁移评估。命令默认使用 `config.settings.dev`，只在本机运行。

```bash
git clone https://github.com/RaM-bugourp/ram-admin.git
cd ram-admin
python -m venv .venv
```

激活虚拟环境：

```bash
# macOS / Linux
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

**终端一：后端**（从仓库根目录、虚拟环境已激活）：

```bash
python -m pip install -r backend/requirements.txt
cd backend
python manage.py migrate --settings=config.settings.dev
python manage.py createsuperuser --settings=config.settings.dev
python manage.py runserver 127.0.0.1:8000 --settings=config.settings.dev
```

`createsuperuser` 会交互询问用户名、邮箱和密码；登录字段为 `username`，创建的 `is_superuser` 用户具有核心管理权限，无需预先绑定 root 角色。自行设置强密码。仓库另有 `init_rbac` 命令，会初始化角色并使用硬编码的 `admin / admin123` 创建演示管理员；它仅适合隔离的本地演示，不属于上述推荐启动步骤。

**终端二：前端**（从仓库根目录）：

```bash
cd frontend
npm ci
npm run dev -- --host localhost --port 5173 --strictPort
```

浏览器打开 **http://localhost:5173**，使用刚创建的用户登录。Vite 将 `/api` 代理到 `http://127.0.0.1:8000`，并启用 `changeOrigin`；开发配置已将 `http://localhost:5173` 列入 `CSRF_TRUSTED_ORIGINS`。请保持这个浏览器入口，不混用 `localhost` 与 `127.0.0.1` 的页面/Cookie，也不要绕过前端代理调用登录。更换域名或端口时需同步核对 Host、Origin 与 CSRF 配置。

开发环境未设置 `DJANGO_SECRET_KEY` 时会生成进程随机密钥，后端重启可能使原有会话失效。项目通过 Django 密码哈希接口存储密码；普通配置未指定 bcrypt，测试配置使用的快速哈希仅用于测试。

## 主要 API

除 CSRF 获取与登录入口外，以下接口均需有效登录；写请求需满足 CSRF 校验。资源读写还需相应权限，具备 `users.write` 也不意味着可以管理任意高权限目标。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/auth/csrf/` | 获取 CSRF Token |
| POST | `/api/auth/login/` | 登录，提交 `username`、`password` |
| POST | `/api/auth/logout/` | 退出登录 |
| GET | `/api/auth/user-info/` | 当前身份、角色与权限 |
| GET | `/api/auth/settings/` | 个人设置与 AI 界面开关状态 |
| POST | `/api/auth/change-password/` | 提交 `old_password`、`new_password` |
| GET | `/api/auth/sessions/` | 本人会话清单 |
| POST | `/api/auth/revoke-session/` | 提交 `{"id":"会话 UUID"}`，撤销本人单个会话 |
| POST | `/api/auth/revoke-other-sessions/` | 空请求体，退出本人其他会话 |
| POST | `/api/auth/revoke-user-sessions/` | 提交 `{"user_id":123}`，仅 root 可全撤目标用户会话 |
| GET / POST | `/api/rbac/users/` | 用户列表/创建 |
| GET / PUT / DELETE | `/api/rbac/users/{id}/` | 用户详情/更新/软删除 |
| POST | `/api/rbac/users/{id}/reset-password/` | 管理员重置密码，仍受目标权限边界约束 |
| GET / POST | `/api/rbac/roles/` | 角色列表/创建 |
| GET / PUT / DELETE | `/api/rbac/roles/{id}/` | 角色详情/更新/删除 |
| GET | `/api/rbac/permissions/` | 权限目录，需 `roles.read` |
| GET | `/api/dashboard/stats/` | 工作台统计，需 `dashboard.read` |
| GET | `/api/audit/logs/` | 审计列表，需 `audit.read` |
| GET | `/api/audit/export/` | CSV 导出，需 `audit.read` |

审计筛选字段为 `action`、`resource`、`outcome`、`actor_id`、`start`、`end`。列表另支持 `page`、`page_size`；导出不接受分页字段。时间须为带时区的 ISO 日期时间，非法日期、倒置范围、未知或重复字段会被拒绝。核心审计没有对外的统计或清理端点。

## 可选 AI 配置

在启动后端前设置进程环境变量。例如 macOS / Linux：

```bash
export AI_UI_ENABLED=true
export OPENAI_API_KEY="你的 Provider Key"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="你的可用模型名"
export AI_MOCK_WHEN_NO_KEY=false
```

PowerShell 使用 `$env:变量名="值"` 的形式。Provider 列表与其他选项见 [base.py](backend/config/settings/base.py)。

`AI_UI_ENABLED=false` 仅默认隐藏前端 AI 入口，**不关闭 AI API**。API 按独立权限规则检查当前 root/superuser 身份；接受 Agent Token 的入口还会单独验证凭证。启用 UI、配置 Provider 与配置 Agent Token 密钥是三件独立的事。

开发默认在没有可用 Provider 时允许 Mock 回复；Mock 不是实际模型调用。`AI_MOCK_WHEN_NO_KEY=false` 可禁止该回退，production 配置固定禁用 Mock。外部 Provider 的连通性与实际模型效果需自行验证。

如需 Agent Token，必须另设随机的专用 `AI_AGENT_TOKEN_SECRET`，至少 32 字符，并独立于 Django 密钥保管。缺少或过短时签发/验证会拒绝，不会回退使用 Django 密钥。Token v2 使用随机凭证、HMAC-SHA256 与完整摘要凭证账本，并逐次核对签发人的当前有效权限。root 可通过 `POST /api/ai/agent-token/issue/` 签发、`POST /api/ai/agent-token/revoke/` 撤销。

旧格式 Token 已失效，需要重新签发。`ai.0002_agent_credentials` 的逆迁移会删除凭证账本，`ai.0003_aiapproval_submitted_by` 包含无法还原原文的数据清理；不要直接回退旧二进制或在生产环境随意逆迁移。这些具体风险不等于“所有迁移都不可逆”。

## 本机 SQLite 运维

仅供拥有目标数据库 OS 访问权限的本机操作者使用。先确认所选 settings 已正确配置并指向获准操作的 SQLite 数据库。以下以**已经按快速开始初始化的开发数据库**为例，在 `backend` 目录执行：

```bash
python manage.py local_ops health --settings=config.settings.dev
python manage.py local_ops backup --settings=config.settings.dev
python manage.py local_ops restore --backup-id <backup返回的32位十六进制ID> --settings=config.settings.dev
```

备份保存在仓库固定的 `.private-ops/backups/` 私有目录，使用 SQLite 在线备份接口；恢复写入新的 `.private-ops/restores/` 目录，目标已存在会拒绝，**不会覆盖 live 数据库，也不执行自动切库**。恢复会核对 schema、完整性、外键、全表全列与迁移账本。

备份含密码哈希、会话与 Token 摘要等敏感数据，不能公开或提交到 Git；Django/Token 密钥不在备份内，应独立保护。同配置密钥下恢复的会话或凭证可能仍有效，恢复副本不要暴露到公网。

如选择 `config.settings.production`，必须事先提供符合校验的 `DJANGO_SECRET_KEY`、明确的 `DJANGO_ALLOWED_HOSTS` 和绝对路径 `DJANGO_DB_PATH`，并配置 HTTPS/代理等部署事项。当前 production 配置仍为 SQLite；其配置存在不代表生产部署、恢复演练或 PostgreSQL 支持已经验收。

## 开发与目录

```text
backend/
  config/          settings 与根路由
  apps/common/    公共模型、异常与 SQLite 运维实现
  apps/rbac/      用户、角色、权限、认证与会话安全
  apps/audit/     核心操作审计列表与 CSV
  apps/ai/        可选 AI、审批与 Agent 凭证
frontend/
  src/            Vue 页面、路由、状态与 API 客户端
docs/             设计文档
changelog/        历史变更记录
```

开发检查命令（各自在对应目录执行）：

```bash
# backend，已激活独立虚拟环境
python manage.py check --settings=config.settings.test
python manage.py test apps.rbac apps.ai --settings=config.settings.test

# frontend
npm ci
npm run typecheck
npm run build
```

后端测试显式使用隔离测试配置，不指向已有业务库。前端 `build` 包含 TypeScript 检查与 Vite 构建；仓库虽有 lint 脚本，但当前依赖未包含 ESLint，不能将其视为已通过的检查。

可继续阅读 [开发运行说明](DEVELOPMENT.md)、[架构说明](ARCHITECTURE.md) 与 [AI 集成设计](docs/ai-integration-design.md)。这些文档含历史设计或开发记录；当前端点与配置以源码为准。生产部署、外部 AI、容量/多 worker、真实设备与安全总审仍需专门验收。

## 授权

当前仓库根目录没有项目级 LICENSE 文件，项目整体授权条款仍待确认。使用或分发前请向权利人核实；第三方依赖的许可证不等同于本项目整体授权。
