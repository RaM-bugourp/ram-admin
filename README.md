# RaM Admin

<div align="center">

![Django](https://img.shields.io/badge/Django-5.2-green?logo=django)
![Vue](https://img.shields.io/badge/Vue-3.5-blue?logo=vue.js)
![Arco Design](https://img.shields.io/badge/Arco%20Design-2.56-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

**企业级后台管理框架 | Django 5 + Vue 3 + Arco Design + DRF**

[快速开始](#快速启动) · [在线文档](#文档) · [架构设计](./ARCHITECTURE.md) · [贡献指南](./CONTRIBUTING.md)

</div>

---

## 项目定位

```
┌─────────────────────────────────────────────────────────────┐
│                      RaM Admin                              │
├─────────────────────────────────────────────────────────────┤
│  ❌ 不是：功能堆砌的大而全系统                               │
│  ✅ 而是：干净、可学、可二次开发的基础框架                   │
│                                                             │
│  适用场景：                                                  │
│  • 学习 Django + Vue 全栈开发                               │
│  • 作为企业后台项目的起点                                    │
│  • 二次开发定制专属管理系统                                  │
│                                                             │
│  核心理念：                                                  │
│  • 代码即文档 —— 详细注释，自解释                           │
│  • 约定优于配置 —— 标准结构，开箱即用                       │
│  • 关注点分离 —— 前后端独立，模块解耦                       │
└─────────────────────────────────────────────────────────────┘
```

## 特性

- ✅ **RBAC 权限模型**：组织/角色/权限/菜单，支持数据权限
- ✅ **动态路由**：后端菜单树 → 前端路由配置
- ✅ **软删除**：数据安全，可追溯可恢复
- ✅ **操作日志**：自动记录所有操作
- ✅ **API 文档**：Swagger UI + ReDoc
- ✅ **代码生成器**：一键生成 CRUD 代码
- ✅ **Docker 支持**：一键容器化部署
- ✅ **详细文档**：架构设计 + 开发指南 + 部署指南

## 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 后端框架 | Django + DRF | 5.2 / 3.15+ | 成熟稳定，企业首选 |
| 数据库 | SQLite / PostgreSQL | — | 开发零配置，生产高性能 |
| 前端框架 | Vue 3 + Vite | 3.5 / 6.2 | 组合式API，开发体验好 |
| UI 组件库 | Arco Design Vue | 2.56+ | 字节开源，设计精美 |
| 状态管理 | Vuex | 4.x | 简单直接 |
| 权限控制 | 自研 RBAC | — | 完全可控，易于定制 |

## 快速启动

### 方式一：一键启动（推荐）

**Windows**:
```bash
# 双击运行
start.bat
```

**Linux/macOS**:
```bash
chmod +x start.sh
./start.sh
```

### 方式二：手动启动

```bash
# 1. 克隆项目
git clone https://github.com/yourname/ram-admin.git
cd ram-admin

# 2. 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# 3. 前端（新终端）
cd frontend
npm install
npm run dev
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/api/docs/ |
| Django Admin | http://localhost:8000/admin/ |

**默认账号**: `admin` / `admin123`

## 项目结构

```
ram-admin/
├── 📁 backend/                 # Django 后端
│   ├── 📁 apps/                # 业务应用
│   │   ├── 📁 user/            # 用户认证
│   │   ├── 📁 rbac/            # RBAC 权限
│   │   ├── 📁 article/         # 文章管理（示例）
│   │   ├── 📁 system/          # 系统管理
│   │   └── 📁 audit/           # 操作日志
│   ├── 📁 tests/               # 测试用例
│   └── 📁 scripts/             # 脚本工具
│
├── 📁 frontend/                # Vue 3 前端
│   └── 📁 src/
│       ├── 📁 api/             # API 接口
│       ├── 📁 views/           # 页面组件
│       ├── 📁 components/      # 通用组件
│       ├── 📁 router/          # 路由配置
│       └── 📁 store/           # Vuex 状态
│
├── 📁 packages/                # 框架核心层
│   └── 📁 core/                # Python 核心（可独立复用）
│       ├── 📁 foundation/      # 基础模型 + Mixin
│       ├── 📁 permissions/     # RBAC 权限
│       └── 📁 audit/           # 审计核心
│
├── 📁 docs/                    # 文档
├── 📄 ARCHITECTURE.md          # 架构设计文档
├── 📄 docker-compose.yml       # Docker 编排
└── 📄 .env.example             # 环境配置模板
```

## 文档

| 文档 | 说明 |
|------|------|
| [架构设计](./ARCHITECTURE.md) | 完整架构设计思路，适合二次开发者阅读 |
| [开发指南](./docs/DEVELOPMENT.md) | 如何添加新模块、编写代码 |
| [部署指南](./docs/DEPLOYMENT.md) | 生产环境部署配置 |
| [API 文档](./docs/API.md) | 接口说明（在线版：/api/docs/） |
| [学习指南](./docs/学习指南.md) | 模块设计思想 + 面试要点 |

## 核心特性详解

### RBAC 权限模型

```
User → UserRole → Role → Permission
                    ↓
                  Menu（菜单可见）
                    ↓
              DataScope（数据范围）
```

- 支持：全部数据 / 本部门 / 本部门及下级 / 仅本人 / 自定义
- 前端：动态路由 + 按钮权限
- 后端：接口权限 + 数据过滤

### 软删除

```python
class Article(BaseAuditModel):  # 继承即获得软删除
    title = models.CharField(max_length=200)

article.delete()  # 实际是 is_deleted = True
Article.objects.all()  # 自动过滤已删除记录
```

### 代码生成器

```bash
python scripts/codegen.py shop Product --fields name:str,price:decimal,stock:int
# 自动生成：models.py, serializers.py, views.py, urls.py
```

## 开发路线

- [x] RBAC 权限模型
- [x] 动态路由
- [x] 软删除
- [x] 操作日志
- [x] API 文档（Swagger）
- [x] 代码生成器
- [x] Docker 支持
- [x] 测试用例
- [ ] WebSocket 支持
- [ ] 异步任务（Celery）
- [ ] 代码生成器前端

## 贡献

欢迎贡献代码！请阅读 [贡献指南](./CONTRIBUTING.md)。

```bash
# 开发流程
git checkout -b feature/your-feature
# 编写代码 + 测试
pytest  # 运行测试
git commit -m "feat: 添加新功能"
git push origin feature/your-feature
# 提交 PR
```

## 致谢

本项目参考了以下开源项目的设计思想：

- [django-vue-adminx](https://github.com/xxx/django-vue-adminx) — RBAC 权限设计参考
- [arco_admin_template](https://github.com/zhaozhentao/arco_admin_template) — 前端模板参考

## 开源协议

[MIT License](./LICENSE) - 可商用，可修改，无需授权。

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star 支持一下！**

Made with ❤️ by RaM

</div>
