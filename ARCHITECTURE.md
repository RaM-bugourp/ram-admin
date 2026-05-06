# RaM Admin 架构设计文档

> **阅读时间：约 15 分钟**
> **适用人群：二次开发者、架构师、代码贡献者**
> **最后更新：2026-04-20**

---

## 一、项目概述

### 1.1 项目定位

RaM Admin 是一个**学习型、生产级**的企业后台管理框架。

```
┌─────────────────────────────────────────────────────────────┐
│                      RaM Admin 定位                         │
├─────────────────────────────────────────────────────────────┤
│  ❌ 不是：功能堆砌的大而全系统                               │
│  ✅ 而是：干净、可学、可二次开发的基础框架                   │
│                                                             │
│  核心理念：                                                  │
│  • 代码即文档 —— 详细注释，自解释                           │
│  • 约定优于配置 —— 标准结构，开箱即用                       │
│  • 关注点分离 —— 前后端独立，模块解耦                       │
│  • 渐进增强 —— 基础功能 + 按需扩展                          │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈选择理由

| 层级 | 技术选择 | 选择理由 |
|------|----------|----------|
| **后端框架** | Django 5 + DRF | 成熟稳定、文档完善、生态丰富、企业级首选 |
| **前端框架** | Vue 3 + Vite | 组合式API、性能优秀、开发体验好 |
| **UI组件库** | Arco Design | 字节开源、设计精美、Vue 3 原生支持 |
| **状态管理** | Vuex 4 | 简单直接、适合中小项目（可选 Pinia） |
| **权限模型** | 自研 RBAC | 完全可控、无黑盒、易于定制 |
| **数据库** | SQLite → PostgreSQL | 开发用 SQLite 零配置，生产用 PG 高性能 |

### 1.3 与同类项目对比

| 特性 | RaM Admin | django-vue-adminx | dvadmin |
|------|-----------|-------------------|---------|
| 代码可读性 | ⭐⭐⭐⭐⭐ 详细注释 | ⭐⭐⭐ | ⭐⭐⭐ |
| 学习曲线 | ⭐⭐⭐⭐⭐ 平缓 | ⭐⭐ 较陡 | ⭐⭐⭐ |
| 功能丰富度 | ⭐⭐⭐ 精简 | ⭐⭐⭐⭐⭐ 丰富 | ⭐⭐⭐⭐ |
| 二次开发 | ⭐⭐⭐⭐⭐ 容易 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 生产就绪 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**结论**：RaM Admin 适合学习和二次开发，django-vue-adminx 适合直接使用。

---

## 二、目录结构设计

### 2.1 整体结构

```
ram-admin/
├── 📁 backend/                 # Django 后端
│   ├── 📁 apps/                # 业务应用（核心）
│   │   ├── 📁 user/            # 用户认证
│   │   ├── 📁 rbac/            # RBAC 权限
│   │   ├── 📁 article/         # 文章管理（示例模块）
│   │   ├── 📁 system/          # 系统管理
│   │   └── 📁 audit/           # 操作日志
│   ├── 📁 ram_admin/           # 项目配置
│   ├── 📁 libcore/             # 核心库（通用工具）
│   ├── 📁 tests/               # 测试用例
│   └── 📁 scripts/             # 脚本工具
│
├── 📁 frontend/                # Vue 3 前端
│   ├── 📁 src/
│   │   ├── 📁 api/             # API 接口封装
│   │   ├── 📁 views/           # 页面组件
│   │   ├── 📁 components/      # 通用组件
│   │   ├── 📁 layout/          # 布局组件
│   │   ├── 📁 router/          # 路由配置
│   │   ├── 📁 store/           # Vuex 状态
│   │   └── 📁 utils/           # 工具函数
│   └── 📄 vite.config.js       # Vite 配置
│
├── 📁 packages/                # 框架核心层（可独立发布）
│   ├── 📁 core/                # Python 核心库
│   │   ├── 📁 foundation/      # 基础模型和 Mixin
│   │   ├── 📁 permissions/     # 权限核心
│   │   ├── 📁 audit/           # 审计核心
│   │   └── 📁 scheduler/       # 任务调度
│   └── 📁 frontend/            # 前端核心组件
│
├── 📁 docs/                    # 文档
├── 📄 docker-compose.yml       # Docker 编排
├── 📄 start.bat / start.sh     # 一键启动
└── 📄 .env.example             # 环境配置模板
```

### 2.2 分层设计理念

```
┌─────────────────────────────────────────────────────────────┐
│                      分层架构图                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              前端层 (Vue 3 + Arco)                   │   │
│  │  views/ → components/ → api/ → store/ → router/    │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │ HTTP/JSON                       │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              接口层 (Django REST Framework)          │   │
│  │  urls.py → views.py → serializers.py               │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              业务层 (apps/*)                         │   │
│  │  user/ + rbac/ + article/ + system/ + audit/       │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              框架层 (packages/core)                  │   │
│  │  foundation/ + permissions/ + audit/ + scheduler/  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              数据层 (Django ORM + Database)          │   │
│  │  models.py → migrations/ → SQLite/PostgreSQL       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**关键设计点**：

1. **packages/core 独立于 Django**
   - 可以被任何 Python 项目复用
   - 不依赖 Django ORM，纯业务逻辑

2. **apps/* 是 Django 应用**
   - 依赖 Django ORM
   - 调用 packages/core 提供的能力

3. **前端完全独立**
   - 只通过 API 与后端通信
   - 可以独立部署到 CDN

---

## 三、核心设计模式

### 3.1 Mixin 模式（核心）

RaM Admin 大量使用 Mixin 模式实现能力组合。

#### 模型层 Mixin

```python
# packages/core/foundation/models.py

class SoftDeleteMixin(models.Model):
    """软删除能力"""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True)
    
    def delete(self):
        # 重写删除行为：标记删除，不物理删除
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

class BaseAuditModel(SoftDeleteMixin):
    """审计字段能力"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, ...)
    updated_by = models.ForeignKey(User, ...)

# 使用示例
class Article(BaseAuditModel):
    """文章模型：自动获得软删除 + 审计字段"""
    title = models.CharField(max_length=200)
    content = models.TextField()
```

**为什么用 Mixin？**

```
┌─────────────────────────────────────────────────────────────┐
│  传统继承（单继承限制）                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  class BaseModel(models.Model):                             │
│      created_at = ...                                       │
│                                                             │
│  class SoftDeleteModel(BaseModel):  # 只能继承一个          │
│      is_deleted = ...                                       │
│                                                             │
│  class Article(SoftDeleteModel):  # 无法再加其他能力        │
│      ...                                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Mixin 模式（能力组合）                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  class Article(SoftDeleteMixin, AuditMixin, CacheMixin):   │
│      # 同时获得：软删除 + 审计 + 缓存                        │
│      ...                                                    │
│                                                             │
│  class Product(SoftDeleteMixin, PriceMixin):               │
│      # 同时获得：软删除 + 价格计算                          │
│      ...                                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 视图层 Mixin

```python
# packages/core/foundation/mixins.py

class AuditOwnerPopulateMixin:
    """自动填充创建人/更新人"""
    
    def perform_create(self, serializer):
        # 创建时自动填 created_by
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        # 更新时自动填 updated_by
        serializer.save(updated_by=self.request.user)

class ActionSerializerMixin:
    """按动作选择序列化器"""
    
    def get_serializer_class(self):
        # list 用 ListSerializer（字段少）
        # retrieve 用 DetailSerializer（字段全）
        return getattr(self, f'{self.action}_serializer_class', 
                       self.serializer_class)

# 使用示例
class ArticleViewSet(
    AuditOwnerPopulateMixin,    # 自动填充审计字段
    ActionSerializerMixin,       # 按动作选序列化器
    viewsets.ModelViewSet
):
    serializer_class = ArticleSerializer
    list_serializer_class = ArticleListSerializer
```

### 3.2 RBAC 权限模型

```
┌─────────────────────────────────────────────────────────────┐
│                    RBAC 权限模型                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐     ┌─────────┐     ┌─────────────┐           │
│  │  User   │────▶│UserRole│◀────│    Role     │           │
│  └─────────┘     └─────────┘     └─────────────┘           │
│       │                               │                     │
│       │                               │                     │
│       ▼                               ▼                     │
│  ┌─────────┐                   ┌─────────────┐             │
│  │ Org     │                   │ Permission  │             │
│  └─────────┘                   └─────────────┘             │
│       │                               │                     │
│       │                               │                     │
│       ▼                               ▼                     │
│  ┌─────────────┐               ┌─────────────┐             │
│  │UserOrg     │               │    Menu     │             │
│  └─────────────┘               └─────────────┘             │
│                                                             │
│  权限检查流程：                                              │
│  1. 用户登录 → 获取用户所有角色                              │
│  2. 角色 → 获取所有权限码                                    │
│  3. 角色 → 获取可见菜单树                                    │
│  4. 前端根据菜单树渲染侧边栏                                 │
│  5. 后端根据权限码校验接口访问                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**数据表关系**：

```sql
-- 用户表
user (id, username, email, is_superuser)

-- 组织表（树形结构）
organization (id, name, code, parent_id, tree_id, lft, rght)

-- 用户-组织关联
user_organization (id, user_id, org_id, is_primary)

-- 角色表
role (id, name, code, data_scope)

-- 用户-角色关联
user_role (id, user_id, role_id)

-- 权限表
permission (id, name, code, http_method, url_pattern)

-- 角色-权限关联
role_permission (id, role_id, permission_id)

-- 菜单表（树形结构）
menu (id, title, path, component, icon, parent_id)

-- 角色-菜单关联
role_menu (id, role_id, menu_id)
```

### 3.3 动态路由设计

```
┌─────────────────────────────────────────────────────────────┐
│                    动态路由流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 用户登录                                                │
│       │                                                     │
│       ▼                                                     │
│  2. 前端调用 GET /api/rbac/menus/tree/                      │
│       │                                                     │
│       ▼                                                     │
│  3. 后端返回该用户的菜单树                                   │
│     [                                                       │
│       {                                                     │
│         "id": 1,                                            │
│         "title": "系统管理",                                │
│         "path": "/system",                                  │
│         "icon": "icon-setting",                             │
│         "children": [                                       │
│           {                                                 │
│             "id": 2,                                        │
│             "title": "用户管理",                            │
│             "path": "/system/user",                         │
│             "component": "system/user/index"                │
│           }                                                 │
│         ]                                                   │
│       }                                                     │
│     ]                                                       │
│       │                                                     │
│       ▼                                                     │
│  4. 前端将菜单树转换为 Vue Router 路由配置                   │
│     {                                                       │
│       path: '/system',                                      │
│       component: Layout,                                    │
│       children: [                                           │
│         {                                                   │
│           path: 'user',                                     │
│           component: () => import('@/views/system/user')   │
│         }                                                   │
│       ]                                                     │
│     }                                                       │
│       │                                                     │
│       ▼                                                     │
│  5. router.addRoute() 动态注册路由                          │
│       │                                                     │
│       ▼                                                     │
│  6. 渲染侧边栏菜单                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**关键代码**：

```javascript
// frontend/src/router/index.js

async function _loadMenuAndRoutes() {
  // 1. 获取菜单树
  const res = await fetch('/api/rbac/menus/tree/')
  const menuTree = await res.json()
  
  // 2. 转换为路由配置
  const routes = _menuTreeToRoutes(menuTree)
  
  // 3. 动态注册
  routes.forEach(route => router.addRoute(route))
}

function _menuTreeToRoutes(tree) {
  return tree.map(menu => ({
    path: menu.path,
    component: () => import(`@/views/${menu.component}.vue`),
    meta: { title: menu.title, icon: menu.icon },
    children: menu.children ? _menuTreeToRoutes(menu.children) : []
  }))
}
```

---

## 四、数据流设计

### 4.1 请求生命周期

```
┌─────────────────────────────────────────────────────────────┐
│                    请求处理流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  浏览器发起请求                                              │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Nginx / Vite Proxy                                  │   │
│  │  /api/* → http://localhost:8000                      │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Django 中间件栈                                     │   │
│  │  SecurityMiddleware                                   │   │
│  │  CorsMiddleware         → CORS 跨域处理              │   │
│  │  SessionMiddleware      → Session 读取               │   │
│  │  CsrfViewMiddleware     → CSRF 校验                  │   │
│  │  AuthenticationMiddleware → 用户认证                 │   │
│  │  OperationLogMiddleware → 操作日志记录               │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  URL 路由匹配                                        │   │
│  │  path('api/article/', include('apps.article.urls')) │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  DRF ViewSet                                         │   │
│  │  ArticleViewSet.list()                               │   │
│  │    → get_queryset()  获取查询集                      │   │
│  │    → filter_queryset() 过滤                          │   │
│  │    → paginate_queryset() 分页                        │   │
│  │    → serializer_class  序列化                        │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  响应返回                                            │   │
│  │  {                                                   │   │
│  │    "list": [...],                                    │   │
│  │    "total": 100,                                     │   │
│  │    "page": 1                                         │   │
│  │  }                                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 前端状态管理

```
┌─────────────────────────────────────────────────────────────┐
│                    Vuex 状态设计                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  store/                                                     │
│  ├── index.js              # 根 Store                       │
│  └── modules/                                               │
│      ├── user.js           # 用户状态                        │
│      └── menu.js           # 菜单状态                        │
│                                                             │
│  user module:                                               │
│  {                                                          │
│    state: {                                                 │
│      id: null,                                              │
│      username: '',                                          │
│      is_superuser: false,                                   │
│      roles: [],                                             │
│      permissions: []                                        │
│    },                                                       │
│    getters: {                                               │
│      hasPermission: (code) => boolean,                      │
│      isLoggedIn: () => boolean                              │
│    },                                                       │
│    actions: {                                               │
│      login(username, password),                             │
│      logout(),                                              │
│      getUserInfo()                                          │
│    }                                                        │
│  }                                                          │
│                                                             │
│  menu module:                                               │
│  {                                                          │
│    state: {                                                 │
│      menuTree: [],        # 菜单树                          │
│      currentMenu: null    # 当前激活菜单                     │
│    },                                                       │
│    actions: {                                               │
│      loadMenuTree(),                                        │
│      setActiveMenu(menu)                                    │
│    }                                                        │
│  }                                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 五、扩展指南

### 5.1 添加新业务模块

**步骤 1：使用代码生成器**

```bash
cd backend
python scripts/codegen.py shop Product --fields name:str,price:decimal,stock:int
```

自动生成：
- `apps/shop/models.py`
- `apps/shop/serializers.py`
- `apps/shop/views.py`
- `apps/shop/urls.py`

**步骤 2：注册应用**

```python
# settings.py
INSTALLED_APPS = [
    ...
    'apps.shop',  # 添加新应用
]
```

**步骤 3：注册路由**

```python
# urls.py
urlpatterns = [
    ...
    path('api/shop/', include('apps.shop.urls')),
]
```

**步骤 4：数据库迁移**

```bash
python manage.py makemigrations shop
python manage.py migrate
```

**步骤 5：添加前端页面**

```javascript
// frontend/src/views/shop/product/list.vue
<template>
  <CrudTable
    :columns="columns"
    api-url="/api/shop/products/"
  />
</template>
```

### 5.2 自定义权限检查

```python
# 方式一：在 ViewSet 中检查
class ArticleViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # 只返回当前用户创建的文章
        return Article.objects.filter(created_by=self.request.user)

# 方式二：使用装饰器
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

@permission_classes([IsAuthenticated])
def my_view(request):
    ...

# 方式三：自定义权限类
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user
```

### 5.3 添加新的 Mixin

```python
# packages/core/foundation/mixins.py

class CacheMixin:
    """缓存 Mixin"""
    
    cache_timeout = 300  # 5分钟
    
    def get_cached_queryset(self):
        cache_key = f'{self.__class__.__name__}:queryset'
        queryset = cache.get(cache_key)
        if queryset is None:
            queryset = self.get_queryset()
            cache.set(cache_key, queryset, self.cache_timeout)
        return queryset

# 使用
class ArticleViewSet(CacheMixin, viewsets.ModelViewSet):
    ...
```

---

## 六、最佳实践

### 6.1 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 模型类 | 大驼峰 | `Article`, `UserRole` |
| 视图集 | 模型名 + ViewSet | `ArticleViewSet` |
| 序列化器 | 模型名 + Serializer | `ArticleSerializer` |
| URL 路由 | 复数形式 | `/api/articles/` |
| 数据库表 | app_model | `article_article` |
| 前端组件 | 大驼峰 | `ArticleList.vue` |
| API 文件 | 小驼峰 | `article.js` |

### 6.2 代码组织

```python
# ✅ 推荐：按功能分文件
apps/article/
├── models.py          # 模型定义
├── serializers.py     # 序列化器
├── views.py           # 视图
├── urls.py            # 路由
├── filters.py         # 过滤器（可选）
├── services.py        # 业务逻辑（可选）
└── tests.py           # 测试

# ❌ 不推荐：所有代码放一个文件
apps/article/
└── __init__.py        # 所有代码都在这里
```

### 6.3 错误处理

```python
# ✅ 推荐：使用自定义异常
from libcore.exceptions import BusinessError

def transfer_money(from_user, to_user, amount):
    if from_user.balance < amount:
        raise BusinessError('余额不足', code='INSUFFICIENT_BALANCE')
    ...

# ❌ 不推荐：直接 raise Exception
def transfer_money(from_user, to_user, amount):
    if from_user.balance < amount:
        raise Exception('余额不足')
```

### 6.4 性能优化

```python
# ✅ 推荐：使用 select_related / prefetch_related
class ArticleViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Article.objects.select_related('created_by').prefetch_related('tags')

# ❌ 不推荐：N+1 查询
class ArticleViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Article.objects.all()  # 每条记录都会查一次 created_by

# ✅ 推荐：使用 only / defer 限制字段
Article.objects.only('title', 'summary')  # 只查需要的字段

# ✅ 推荐：使用索引
class Article(models.Model):
    title = models.CharField(max_length=200)
    
    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['created_at']),
        ]
```

---

## 七、常见问题

### Q1: 为什么不用 Pinia 而用 Vuex？

**A**: 两者都可以。Vuex 更简单直接，适合中小项目。如果团队熟悉 Pinia，可以迁移：

```bash
npm uninstall vuex
npm install pinia
```

### Q2: 为什么不用 JWT 而用 Session？

**A**: Session 认证更安全，适合传统 Web 应用。JWT 适合移动端和 SPA 无状态场景。需要 JWT 可以加装 `djangorestframework-simplejwt`。

### Q3: 如何支持多租户？

**A**: 通过 `owner_organization` 字段实现数据隔离：

```python
class TenantMixin:
    def get_queryset(self):
        return super().get_queryset().filter(
            owner_organization=self.request.user.primary_org
        )
```

### Q4: 如何添加 WebSocket 支持？

**A**: 安装 Django Channels：

```bash
pip install channels daphne
```

---

## 八、贡献指南

### 8.1 开发流程

```
1. Fork 仓库
2. 创建分支：git checkout -b feature/your-feature
3. 编写代码 + 测试
4. 运行测试：pytest
5. 提交 PR
```

### 8.2 代码规范

- Python: 遵循 PEP 8，使用 `black` 格式化
- JavaScript: 使用 `prettier` 格式化
- 提交信息: 遵循 Conventional Commits

### 8.3 文档规范

- 所有公开 API 必须有 docstring
- 复杂逻辑必须有注释
- README 保持更新

---

## 九、版本规划

| 版本 | 功能 | 状态 |
|------|------|------|
| v1.0 | 基础 RBAC + CRUD | ✅ 完成 |
| v1.1 | API 文档 + 测试 | 🔄 进行中 |
| v1.2 | 代码生成器 | 📅 计划中 |
| v2.0 | WebSocket + 异步任务 | 📅 计划中 |

---

**文档结束**

如有疑问，请提交 Issue 或 PR。
