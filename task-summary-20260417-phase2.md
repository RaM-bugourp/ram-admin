# 任务总结：RaM-Admin 开源框架搭建（2026-04-17 第二阶段）

## 目标
将框架补全为可运行的完整开源项目，能够实际启动、登录、CRUD。

## 本次新增交付物

### 开源基础设施
- `LICENSE` — MIT 协议
- `.gitignore` — Python + Node.js 联合忽略
- `.github/workflows/ci.yml` — GitHub Actions CI（后端测试 + 前端构建 + 代码质量）
- `CONTRIBUTING.md` — 贡献指南（分支规范 / 代码规范 / 测试命令）
- `frontend/.env` — 环境变量配置
- `frontend/index.html` — 前端入口 HTML

### 后端可运行项目（backend/）
- `ram_admin/settings.py` — 完整 Django 配置（INSTALLED_APPS / DRF / CORS / 日志）
- `ram_admin/urls.py` — 主路由（含 DRF DefaultRouter）
- `ram_admin/wsgi.py` — WSGI 入口
- `manage.py` — Django 管理脚本
- `requirements.txt` — 运行依赖（含 django-mptt）
- `requirements-dev.txt` — 开发依赖（pytest / ruff / eslint）
- `pytest.ini` — 测试配置
- `core/__init__.py` — packages/core 封装层（自动 sys.path 注入）
- `core/exceptions.py` — 全局异常处理器（统一错误格式）

### Django Apps（5个）
| App | 文件 | 说明 |
|-----|------|------|
| `apps.user` | models/serializers/views/urls | 自定义 User + 认证接口 |
| `apps.rbac` | models/serializers/views/urls | Organization(M) + Menu + Permission + Role |
| `apps.article` | models/serializers/views/urls | 文章 CRUD（完整套餐示例） |
| `apps.system` | views/urls | 菜单树 / 健康检查 / 指标 |
| `apps.audit` | models/middleware | OperationLog 代理（避免循环导入） |

### 前端可运行项目（frontend/）
| 文件 | 说明 |
|------|------|
| `package.json` | 依赖 + npm scripts |
| `vite.config.js` | Vite 配置 + API 代理 |
| `src/main.js` | Vue 3 入口 |
| `src/App.vue` | 根组件 |
| `src/style.css` | 全局样式 |
| `src/api/user.js` | 用户认证 API |
| `src/api/menu.js` | 菜单 API |
| `src/api/article.js` | 文章 CRUD API |
| `src/router/index.js` | 完整路由（静态 + 动态 + 守卫） |
| `src/store/modules/user.js` | 修复后的 user store |
| `src/views/login/index.vue` | 登录页 |
| `src/views/dashboard/index.vue` | Dashboard |
| `src/views/article/list.vue` | 文章列表（ProTable 示例） |
| `src/views/404.vue` | 404 页面 |

### 初始化脚本
- `scripts/init_db.py` — 一键：migrate + 创建超管 + 示例菜单 + 管理员角色

## 关键架构决策

### 1. 循环导入解决方案
```
apps/user/models.py ↔ apps/rbac/models.py 循环依赖
解决方案：
  - User.model 用字符串引用：ForeignKey('apps.rbac.Organization')
  - Organization 延迟导入（get_primary_organization 方法内导入）
  - UserOrganization 在 apps.rbac 之后才被访问，安全
```

### 2. packages/core ↔ Django apps 桥接
```
packages/core/           — 纯 Python，可独立复用
backend/core/           — Django 项目层，自动 sys.path 注入
apps.audit.middleware   — 代理层，避免 apps ↔ packages 循环
```

### 3. 前端路由重写
```
packages/frontend/        — 框架层路由（占位）
frontend/src/           — 可运行项目路由（完整实现）
```
> packages/frontend/ 中的路由代码保留作为参考/模板。

## 启动方式

```bash
# 后端
cd backend
python -m venv venv && .\venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_db.py
python manage.py runserver

# 前端
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
# 登录：admin / admin123
```

## 下一步工作
1. **跑通实际项目** — 验证 migrate / 登录 / CRUD 是否正常
2. **完善单元测试** — pytest 测试覆盖率
3. **前端 ProTable/ProForm** — 通用业务组件
4. **GitHub 仓库创建** — 初始化 git / 推送到远程
