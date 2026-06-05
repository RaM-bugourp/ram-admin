# Ram-Adminx

> 该项目为重构复现，原项目仓库https://github.com/niezhicheng/django-vue-adminx  
>基于 Django 5.2 + Vue 3 + Arco Design 的现代化后台管理系统，提供 RBAC 权限、代码生成器、操作日志、任务调度等企业级功能。

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green)](https://djangoproject.com)
[![Vue](https://img.shields.io/badge/Vue-3.x-brightgreen)](https://vuejs.org)
[![Arco Design](https://img.shields.io/badge/Arco_Design-2.x-165dff)](https://arco.design/vue)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 功能特性

### 权限管理
- **RBAC 权限控制**：基于角色的访问控制，支持菜单、按钮、API 三级权限
- **数据权限**：基于 MPTT 部门树的行级数据隔离，用户只能看本部门及子部门数据
- **动态菜单**：菜单从数据库加载，前端动态注册路由，新增页面无需重构建

### 系统管理
- **用户管理**：增删改查、密码重置、角色分配、部门绑定
- **角色管理**：角色创建、权限分配、菜单绑定
- **菜单管理**：多级菜单树、图标选择、路由配置、权限码绑定
- **部门管理**：多级组织架构（MPTT 树），支持部门级别的数据权限
- **权限管理**：细粒度权限控制，resource:action 格式

### 代码生成器
- **一键生成 CRUD**：根据 Model 定义自动生成前后端完整代码
- **前后端覆盖**：Model / Service / ViewSet / Serializer / Vue 页面 / API 调用
- **自动注册**：生成后自动注册路由、创建菜单和权限

### 操作日志
- **中间件自动捕获**：记录所有 API 请求的方法、路径、参数、响应
- **敏感数据过滤**：自动过滤密码、Token 等敏感字段
- **多维度查询**：按用户、操作类型、时间范围筛选

### 数据导出
- **流式 CSV 导出**：支持大数据量流式导出，不撑爆内存
- **权限独立**：导出权限与查看权限分离，能看不等于能导出

### 任务调度
- **Cron 表达式**：支持标准 Cron 定时任务配置
- **任务管理**：创建、编辑、启用/禁用、立即执行

### 系统监控
- **仪表盘**：CPU、内存、磁盘、网络实时监控
- **数据统计**：用户、角色、菜单、权限数量统计

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | Django 5.2 + DRF | RESTful API |
| 数据库 | PostgreSQL 16 | 主数据库 |
| 缓存 | Redis 7 | 缓存 + Celery 消息队列 |
| 任务队列 | Celery 5.4 | 异步任务 |
| 前端 | Vue 3 + Composition API | SPA |
| UI | Arco Design Vue | 字节跳动企业级组件库 |
| 状态管理 | Vuex 4 | 集中式状态管理 |
| 构建 | Vite | 开发构建 |
| 语言 | TypeScript | 类型安全 |
| 容器化 | Docker Compose | 一键部署 |

---

## 快速开始

### 环境要求

- Python 3.13+
- Node.js 22+
- PostgreSQL 16+
- Redis 7+


### 默认账号

| 用户名 | 密码 |
|--------|------|
| admin | admin123 |

---

## Docker 部署

```bash
cp .env.example .env   # 编辑环境变量
docker compose up -d
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost |
| 后端 API | http://localhost:8000 |
| 数据库 | localhost:5432 |

---

## 项目结构

```
django-vue-adminx/
├── backend/
│   ├── apps/
│   │   ├── common/          # 公共模块：BaseModel、BaseManager、异常处理
│   │   ├── rbac/            # RBAC：用户、角色、权限、菜单、部门
│   │   ├── audit/           # 操作日志：审计模型、中间件
│   │   ├── codegen/         # 代码生成器
│   │   └── tasks/           # 任务调度
│   ├── config/
│   │   └── settings/        # 配置：base / dev / prod / test
│   ├── manage.py
│   └── requirements.txt
│
├── front-end/
│   ├── src/
│   │   ├── api/             # Axios 封装 + 按模块 API
│   │   ├── views/           # 页面组件（Dashboard、User、Role...）
│   │   ├── components/      # 公共组件 + 业务组件
│   │   ├── router/          # 动态路由注册
│   │   ├── store/           # Vuex 4 状态管理
│   │   └── utils/           # 工具函数
│   ├── package.json
│   └── vite.config.ts
│
├── deploy/
│   └── nginx.conf           # Nginx 反代配置
├── docker-compose.yml
└── .env.example
```

## 开发模板
```


```

---

## API 概览

### 认证

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/auth/login/` | 登录 |
| POST | `/api/auth/logout/` | 登出 |
| GET | `/api/auth/user-info/` | 当前用户信息 |

### 用户管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/rbac/users/` | 用户列表（分页+搜索+过滤） |
| POST | `/api/rbac/users/` | 创建用户 |
| GET | `/api/rbac/users/{id}/` | 用户详情 |
| PUT | `/api/rbac/users/{id}/` | 更新用户 |
| DELETE | `/api/rbac/users/{id}/` | 删除用户（软删除） |
| GET | `/api/rbac/users/?_export=csv` | 导出 CSV |

### 角色 & 权限

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/rbac/roles/` | 角色列表 |
| POST | `/api/rbac/roles/` | 创建角色 |
| GET | `/api/rbac/permissions/` | 权限列表 |

### 菜单

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/rbac/menus/` | 当前用户菜单树 |
| GET | `/api/rbac/menus/all/` | 全部菜单（管理员） |

### 部门

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/rbac/departments/` | 部门树 |
| POST | `/api/rbac/departments/` | 创建部门 |

### 操作日志

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/audit/logs/` | 日志列表（支持多维度过滤） |
| GET | `/api/audit/logs/{id}/` | 日志详情 |

---

## 常见问题

**登录后页面空白？**
检查用户是否分配了角色、角色是否分配了权限。运行 `python manage.py init_rbac` 重新初始化。

**API 请求 403？**
确认已登录（Session 认证），检查用户权限。Session Cookie 需同域，开发环境用 Vite proxy。

**代码生成器生成失败？**
检查 app_label 和 model_name 是否正确，字段配置是否完整。查看后端日志。

---

## 许可证

MIT License
