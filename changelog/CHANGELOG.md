# 更新日志

> 按日期倒序，记录每次版本迭代的功能变更和问题修复。

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

## 2026-06-04 ~ 2026-06-08 — v0.2.0

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
