# 📋 RaM-Admin 框架开发工作日志

> 时间：2026-04-17
> 目标：保守开发一个干净、可学、可二次开发的 Django+Vue3 Admin 基础框架
> 策略：不做多余功能，框架代码全注释、可解释、面试可答

---

## 目录结构

```
ram-admin/
├── packages/
│   ├── core/                    # 框架核心（纯Python，无Django依赖）
│   │   ├── foundation/          # 抽象基类 + Mixin
│   │   ├── permissions/         # RBAC 权限装饰器
│   │   ├── audit/               # 操作日志
│   │   ├── scheduler/           # 任务调度
│   │   └── codegen/            # 代码生成
│   │
│   ├── backend/                 # Django 应用封装
│   │   ├── settings.py          # 预设配置
│   │   ├── urls.py              # 路由蓝图
│   │   └── apps/                # Django apps
│   │       ├── rbac/            # 权限管理
│   │       ├── audit/           # 审计日志
│   │       ├── system/          # 系统管理
│   │       └── curdexample/     # 示例模块
│   │
│   └── frontend/               # Vue3 前端封装
│       └── src/
│           ├── core/            # 核心 store/router/axios
│           ├── components/       # 通用组件
│           ├── layout/         # 布局系统
│           └── views/          # 页面
│
├── docs/                        # 学习文档
└── examples/                   # 示例项目
```

---

## 开发阶段

### 阶段 1 ✅ 项目结构初始化（2026-04-17）
- [x] 创建目录结构
- [x] 编写每个目录的用途说明

### 阶段 2 ✅ 后端 Foundation 层（模型基类 + Mixin）✅
- [x] BaseAuditModel（含 SoftDeleteMixin）
- [x] SoftDeleteMixin（delete() 重写 + 查询过滤）
- [x] AuditOwnerPopulateMixin（perform_create/update 自动填充）
- [x] ActionSerializerMixin（get_serializer_class 重写）
- [x] StandardPagination（含元信息：page/total_pages）
- [x] `__init__.py` 统一导出

### 阶段 3 ✅ 后端 RBAC 权限层 ✅
- [x] Menu / Permission / Role / UserRole 模型
- [x] Organization / UserOrganization 模型
- [x] RBACPermission（URL 正则匹配）
- [x] RBACPermissionByCode（权限码精确模式）
- [x] DataScopeFilter（数据范围过滤）
- [x] `__init__.py` 统一导出

### 阶段 4 ✅ 后端 Audit 日志层 ✅
- [x] OperationLog 模型（GenericForeignKey）
- [x] OperationLogMiddleware（process_request + process_response）
- [x] 敏感字段过滤 + 客户端 IP 提取 + 错误提取

### 阶段 4.5 ✅ 后端 Scheduler 调度层 ✅
- [x] APScheduler 单例 + 启动/停止钩子
- [x] cron_task / interval_task 装饰器

### 阶段 5 ✅ 前端 Core 层 ✅
- [x] axios 封装（请求拦截 + CSRF + 响应分类处理 + DRF 分页适配）
- [x] user store（login / getUserInfo / logout / getters）
- [x] menu store（getMenuTree / SET_MENU_TREE / flatMenuList）
- [x] store/index.js 根模块

### 阶段 6 ✅ 路由层 ✅
- [x] beforeEach 全局守卫（登录检查 → 菜单加载 → 动态路由）
- [x] menuTreeToRoutes（递归路径拼接）
- [x] findFirstMenuPath / catchAll 404

### 阶段 7 ✅ 前端 Layout 层 ✅
- [x] layout/content.vue（整体布局 + 过渡动画）
- [x] layout/navbar.vue（Logo + 用户下拉）
- [x] layout/sidebar.vue（菜单渲染 + 折叠 + 高亮）

### 阶段 8 ✅ 文档 ✅
- [x] README.md
- [x] docs/学习指南.md（设计思想 + 面试问答）
- [x] WORK_LOG.md（本文档）

---

## 核心设计决策记录

### 决策1：为什么用 Mixin 而不是继承？
**问题**：是让模型继承 BaseAuditModel，还是用 Mixin 注入字段？
**选择**：Mixin
**原因**：
- Python 单继承限制多，Mixin 更灵活
- 一个模型可以同时拥有 SoftDeleteMixin + AuditOwnerPopulateMixin
- Django 的 abstract=True 基类本身就是一个 Mixin，但通过 DRF ViewSet 的 Mixin 可以覆盖 perform_create/update

### 决策2：RBAC 权限用 URL 匹配还是代码权限？
**问题**：原项目用 URL 正则匹配，有维护成本
**选择**：两种模式都保留，但推荐代码权限
- URL 匹配：向后兼容，适合快速接入
- 代码权限：代码即权限定义，git 可追踪，适合团队协作
- 推荐用装饰器 `@rbac_permission('user:list')` 而不是数据库注册

### 决策3：前端状态管理用 Vuex 还是 Pinia？
**问题**：原项目用 Vuex，但 Vue3 官方推荐 Pinia
**选择**：暂时保持 Vuex
**原因**：
- 原项目稳定用 Vuex，无迁移必要
- Vuex 足够用，Pinia 是可选升级
- 但 axios 封装和 store 模块划分要学习其设计思想

---

## 学习路径（面试可答）

### Q1：Django 如何实现软删除？
**A**：
1. 模型加 `is_deleted` 布尔字段，默认 False
2. QuerySet 层面覆盖 `get_queryset()`，自动过滤 `is_deleted=False`
3. `perform_destroy` 改为 `instance.is_deleted = True; instance.save()`
4. 恢复时加 `restore()` 方法

### Q2：RBAC 权限系统的设计思路？
**A**：
1. 用户-角色-权限三层模型（中间表解除多对多）
2. 权限粒度：菜单级（前端控制）+ API级（后端控制）+ 数据级（数据库过滤）
3. 数据权限：组织树过滤（ALL/DEPT/SELF/CUSTOM）
4. 动态权限：用户登录时加载权限列表到 Session，前端根据权限码显示菜单

### Q3：DRF 的认证和权限体系如何工作？
**A**：
1. `AuthenticationClasses`：从请求中提取用户（Session/JWT/Token）
2. `PermissionClasses`：检查用户是否有权访问该视图
3. 执行顺序：认证 → 权限检查 → throttling（限流）→ 执行视图

### Q4：Vue3 的权限控制怎么做？
**A**：
1. 路由守卫 `beforeEach` 中检查登录状态
2. 登录成功后从后端加载菜单树 + 权限码列表
3. 前端路由由菜单树动态生成
4. 按钮级别用 `v-if="hasPermission('xxx:yyy')"` 控制
5. 后端每个 API 同时检查权限码，不依赖前端控制

### Q5：中间件在 Django 中的位置？
**A**：
```
请求进来：Middleware_1.process_request → ... → Middleware_N.process_request
         ↓
      URL dispatch（路由匹配）
         ↓
视图函数/ViewSet 执行
         ↓
响应回去：Middleware_1.process_response ← ... ← Middleware_N.process_response
```
操作日志中间件放在 `process_response` 阶段，记录完就放行，不影响主流程。
