# 更新日志

> 按日期倒序，记录每次版本迭代的功能变更和问题修复。

---

## 2026-06-16 — v1.0.2

### 新增功能 — 操作审计日志模块

- **AuditLog 模型** — 12 种操作类型（LOGIN/LOGOUT/LOGIN_FAIL/CREATE/UPDATE/DELETE/EXPORT/APPROVE/REJECT/PASSWORD_RESET/ASSIGN_ROLE/OTHER），8 种资源类型（auth/user/role/dashboard/ai_chat/ai_approval/ai_audit/other），记录 IP / UA / 详情 / 扩展 JSON
- **审计埋点** — 集成到登录/登出（`auth_views.py`）、用户 CRUD + 密码重置（`user_views.py`）、角色 CRUD（`role_views.py`），使用统一的 `log_audit()` 工具函数
- **审计 API** — `GET /api/audit/logs/` 分页列表 + 多维过滤，`GET /api/audit/logs/stats/` 统计聚合，`DELETE /api/audit/logs/cleanup/` 清理过期日志，`GET /api/audit/logs/actions/` / `resources/` 枚举选项
- **审计前端页面** — 4 张统计卡片（总日志/今日操作/今日登录/操作类型数），过滤栏（操作类型/资源类型/用户名搜索/日期范围选择器），分页表格（时间/用户/操作/资源/详情/IP/UA），清理弹窗（仅 root 可见，7-365 天可配）

### 问题修复

- **登录跳转 Bug** — 修复 `LoginView.vue` 和 `store/user.ts` 中 `await` 缺失导致的竞态问题：`router.push()` 在 store 状态更新前执行，路由守卫检查 `isAuthenticated` 返回 false 拦截跳转
- **表单提交 Bug** — Arco Design `<a-form @submit>` 的 async handler 未调用 `ev.preventDefault()`，浏览器原生表单提交导致页面硬刷新回 `/login`
- **401 拦截器递归** — `client.ts` 的 401 拦截器在 `logout()` 后又触发了自身 → 添加 `isLoggingOut` 互斥锁
- **TypeScript 构建错误** — 修复 `MainLayout.vue` 中 `IconBell`→`IconNotification`、`AINotificationView.vue` 同样、`types/ai.ts` 中 `AIAnalyzeResponse` 接口分离、`AIApprovalView.vue` 中缺少 `:model` 的错误

### 详细记录
- [v1.0.2 审计日志实现](./2026-06-16_v1.0.2_审计日志.md)

---

## 2026-06-09 — v0.3.0

### 新增功能
- 三级角色体系（root / BOSS / user），BOSS 全局唯一
- 角色管理页面（RoleListView / RoleFormDialog）
- 权限控制：`IsAdminOrReadOnly` 后端类 + 前端 `isAdmin` getter
- 用户表单多角色分配器，列表角色标签显示
- Dashboard 实时统计数据（用户数/活跃/角色/分配）

### 问题修复
- 权限系统空白（所有认证用户均可写）
- 软删除用户仍可登录 → backends.py 加 is_deleted 过滤
- 用户列表不过滤已删除记录
- last_login_at 与 Django 内置 login() 冲突
- 前端 Store 缺少 roles 状态
- 登录/user-info 不返回角色列表

### 详细记录
- [v0.3.0 更新总结](./2026-06-09_v0.3.0_更新总结.md)
- [P0 权限修复](./2026-06-09_P0权限修复.md)
- [P1/P2 修复](./2026-06-09_P1P2修复.md)
- [权限管理 v0.3.0 开发记录](./2026-06-09_权限管理_v0.3.0.md)
- [配置清单](./CONFIG.md)

---

## 2026-06-09 — v0.4.0 规划中

### AI 集成设计（docs/ai-integration-design.md）

核心设计决策：
- **N+1 故障转移**：OpenAI(主) → DeepSeek(备) → QClaw(兜底)，熔断器自动切换
- **Root 权限守卫**：`RootOnlyAI` 权限类，只有 root 可调用 AI
- **Agent 两阶段审批**：Agent 写操作必须 root 审批后才执行
- **完整审计链**：谁调用 / 调了哪个 Provider / 是否故障转移 / Agent 操作谁审批
- **Root 告警**：Provider 故障时自动通知所有 root 账户

详细设计：参见 [docs/ai-integration-design.md](../docs/ai-integration-design.md)

### 已实现
- Django 5.2 + Vue 3 + Arco Design 项目架构搭建
- 自定义 User 模型（AbstractBaseUser）+ Session + CSRF 认证
- 用户管理 CRUD（列表/创建/编辑/软删除/密码重置）
- 基础 RBAC 模型（User / Role / UserRole）
- ViewSet → Service → Manager → Model 四层架构
- 前端登录页、仪表盘（占位）、用户管理页

### 架构设计
- 详见 [ARCHITECTURE.md](../ARCHITECTURE.md)
- 详见 各模块的 [docs/](../docs/) 设计文档
