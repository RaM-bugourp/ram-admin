# ram-adminx 项目架构文档

> 包含登陆＆用户表单模块的小型demo

---

## 1. 技术栈

```
┌─────────────────────────────────────────────────────┐
│                    技术选型                           │
├──────────────┬──────────────────────────────────────┤
│ 前端 (5173)  │ Vue 3 + Vite + Arco Design + Vuex    │
│              │ + Vue Router + Axios + TypeScript     │
├──────────────┼──────────────────────────────────────┤
│ 后端 (8000)  │ Django 5 + Django REST Framework     │
│              │ + SQLite (开发)                       │
├──────────────┼──────────────────────────────────────┤
│ 通信方式      │ HTTP RESTful API + Session Cookie    │
│              │ + CSRF Token (双重保护)               │
└──────────────┴──────────────────────────────────────┘
```

---

## 2. 整体架构图

```
用户浏览器
    │
    │  http://localhost:5173
    ▼
┌──────────────────────────────────────────────────────────────┐
│                    Vite Dev Server (:5173)                    │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Vue Router  │──│  Page Views  │──│   Vuex Store      │  │
│  │  (路由守卫)   │  │  (Login/User │  │  (user/isAuth)    │  │
│  │              │  │   Dashboard) │  │                    │  │
│  └─────────────┘  └──────┬───────┘  └───────────────────┘  │
│                          │                                   │
│                    Axios Client                              │
│                  (withCredentials + CSRF)                    │
└──────────────────────────┬───────────────────────────────────┘
                           │  Proxy: /api → :8000
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                  Django Server (:8000)                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              MIDDLEWARE 管道 (洋葱模型)                 │   │
│  │                                                      │   │
│  │  CORS → Security → Session → Common → CSRF → Auth   │   │
│  │                                                      │   │
│  │  每个请求依次穿过这些中间件，逐层检查和加工              │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  URL Router                          │   │
│  │                                                     │   │
│  │  /api/auth/     → AuthViewSet    (login/logout)     │   │
│  │  /api/rbac/users/ → UserViewSet  (CRUD)             │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              LAYERED ARCHITECTURE                     │   │
│  │                                                     │   │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐        │   │
│  │  │ ViewSet  │ → │ Service  │ → │ Manager  │        │   │
│  │  │  (接口)   │   │ (业务)    │   │ (查询)    │        │   │
│  │  └──────────┘   └──────────┘   └────┬─────┘        │   │
│  │       ↕                             │               │   │
│  │  ┌──────────┐               ┌───────▼──────┐       │   │
│  │  │Serializer│               │    Model     │       │   │
│  │  │(数据转换) │               │  (ORM/表结构) │       │   │
│  │  └──────────┘               └──────┬───────┘       │   │
│  │                                     │               │   │
│  └─────────────────────────────────────┼───────────────┘   │
│                                        ▼                    │
│                              ┌──────────────────┐           │
│                              │     SQLite       │           │
│                              │   (db.sqlite3)   │           │
│                              └──────────────────┘           │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. 一次完整请求的生命周期

以「用户在前端页面点击"新建用户"按钮」为例，展示数据如何从浏览器一路走到数据库再回来：

```
[1] 用户点击"新建用户"
     │
[2]  Vue 组件 UserFormDialog.vue
     │  → 表单校验 (Arco Form validate)
     │  → 调用 userApi.create({ username, email, password, is_active })
     │
[3]  Axios Client (src/api/client.ts)
     │  → POST http://localhost:5173/api/rbac/users/
     │  → 自动附带 Cookie (sessionid + csrftoken)
     │  → 自动附加 Header: X-CSRFToken
     │
[4]  Vite Proxy
     │  → 将 /api/* 代理到 http://127.0.0.1:8000
     │  → 这个过程对前端代码完全透明
     │
[5]  Django 接收请求 (8000)
     │
[6]  Middleware 管道:
     │  → CORS: 检查跨域 → 放行 (dev: CORS_ALLOW_ALL_ORIGINS)
     │  → Session: 从 Cookie 中提取 sessionid → 查数据库 → 得到 user 对象
     │  → CSRF: 验证 X-CSRFToken 与 Cookie 中的 csrftoken 匹配
     │  → Auth: 将 user 挂到 request.user 上
     │
[7]  URL Router: /api/rbac/users/ → UserViewSet.create()
     │
[8]  Permission Check: IsAuthenticated → request.user 存在 ✓
     │
[9]  Serializer: UserCreateSerializer(data=request.data)
     │  → 校验: username≥3位, email格式, password≥6位
     │  → 校验通过 → validated_data = {username, email, password, is_active}
     │
[10] Service: UserService.create_user(validated_data)
     │  → 检查用户名/邮箱是否重复
     │  → User.objects.create_user(username, email, password)
     │  → Model.set_password() → make_password() 哈希 (bcrypt)
     │  → Model.save() → INSERT INTO rbac_users
     │  → @transaction.atomic 保证原子性
     │
[11] 返回: Response → JSON → 浏览器
     │
[12] 前端: UserFormDialog 收到成功响应
     │  → Message.success('创建成功')
     │  → emit('success') → UserListView 刷新列表
```

---

## 4. 后端分层架构 (逐层详解)

### 4.0 设计理念：为什么分层？

```
❌ 坏做法 (所有逻辑堆在 View 里):
    def create(self, request):
        if User.objects.filter(username=request.data['username']).exists():
            return Response({'error': '重复'})
        user = User.objects.create(...)
        # 300 行之后...

✅ 好做法 (每层职责单一):
    ViewSet  → 只负责 HTTP 相关 (请求解析、响应包装)
    Service  → 只负责业务逻辑 (校验、事务、编排)
    Manager  → 只负责数据库查询封装
    Model    → 只负责表结构定义
```

### 4.1 入口：路由 (URL Router)

```
config/urls.py          ← 根路由，挂载所有子路由
├── /api/auth/          → apps/rbac/urls_auth.py → AuthViewSet
│   ├── POST /login/          登录
│   ├── POST /logout/         登出
│   ├── GET  /user-info/      获取当前用户信息
│   └── GET  /csrf/           获取 CSRF Token
│
└── /api/rbac/users/    → apps/rbac/urls_user.py → UserViewSet
    ├── GET    /                      列表 (分页+搜索)
    ├── POST   /                      创建
    ├── GET    /{id}/                  详情
    ├── PUT    /{id}/                  更新
    ├── DELETE /{id}/                  软删除
    └── POST   /{id}/reset-password/  重置密码
```

**路由是怎么匹配的？**
```
用户请求: POST /api/rbac/users/5/reset-password/

Django 处理过程:
1. config/urls.py 中匹配到 /api/rbac/users/
2. 剩余路径 5/reset-password/ 交给 apps/rbac/urls_user.py
3. DefaultRouter 为 UserViewSet 自动生成以下路由:
   - ^$                               → list (GET) / create (POST)
   - ^{pk}/$                          → retrieve / update / destroy
   - ^{pk}/reset-password/$           → reset_password action ← 匹配!
4. 调用 UserViewSet.reset_password(request, pk="5")
```

### 4.2 ViewSet 层 (HTTP 接口)

**职责**：接收 HTTP 请求 → 参数解析 → 调用 Service → 返回 HTTP 响应

```python
# 核心代码解读: UserViewSet

class UserViewSet(viewsets.GenericViewSet):
    # 所有接口都需要登录
    permission_classes = [IsAuthenticated]

    # 不同 Action 使用不同 Serializer
    def get_serializer_class(self):
        return {
            'create': UserCreateSerializer,      # 创建用的字段: username, email, password, is_active
            'update': UserUpdateSerializer,      # 更新用的字段: 全部可选
            'reset_password': UserResetPasswordSerializer,  # 只需要 password
        }.get(self.action, UserOutputSerializer) # 默认输出用

    def list(self, request):
        # ① 从 URL 参数中提取 page, page_size, search
        # ② 调用 Service 获取分页数据
        # ③ 用 OutputSerializer 序列化为 JSON
        # ④ 返回 {data: [...], pagination: {...}}

    def create(self, request):
        # ① Serializer 校验输入数据
        # ② 调用 Service.create_user()
        # ③ 返回 201 Created
```

**关键概念: Action 路由**
```
GenericViewSet 通过 HTTP Method 自动分发:
  GET    /users/       → list()
  POST   /users/       → create()
  GET    /users/1/     → retrieve()
  PUT    /users/1/     → update()
  DELETE /users/1/     → destroy()

@action 装饰器注册自定义路由:
  @action(detail=True, methods=['post'], url_path='reset-password')
  → POST /users/1/reset-password/  →  reset_password()
```

### 4.3 Service 层 (业务逻辑)

**职责**：实现业务规则，不关心 HTTP，不关心 JSON

```python
# Service 特点:
# ① 使用 @transaction.atomic 保证数据一致性
# ② 使用 BusinessError 抛出结构化异常
# ③ 输入是 Python dict，输出是 Model 实例/Dict

class UserService:
    @transaction.atomic
    def create_user(self, data: dict) -> User:
        # 1. 业务校验：用户名/邮箱不重复
        if User.objects.filter(username=data['username']).exists():
            raise BusinessError(message='用户名已存在', code='DUPLICATE_USERNAME')

        # 2. 创建用户 (密码自动哈希)
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
        )

        # 3. 分配角色 (如果有)
        if data.get('role_ids'):
            # bulk_create: 一条SQL插入多条，比循环 save 快 100 倍
            UserRole.objects.bulk_create([
                UserRole(user=user, role_id=rid)
                for rid in data['role_ids']
            ])

        return user
```

**为什么 @transaction.atomic 重要？**
```
场景: 创建用户 + 分配角色
  → 如果创建用户成功，但插入 UserRole 时报错
  → 没有事务: 会留下一个"孤儿用户"(没角色)
  → 有事务: 整个操作回滚，数据库还是干净的
```

### 4.4 Manager 层 (查询封装)

**职责**：封装高频查询，提供语义化方法名

```python
class BaseManager(models.Manager):
    """核心黑魔法: 自动过滤已删除记录"""

    def get_queryset(self):
        # 重写默认查询集 → 自动追加 is_deleted=False 条件
        return super().get_queryset().filter(is_deleted=False)

    def with_deleted(self):
        # 特殊场景下需要查已删除记录 (如管理员后台)
        return super().get_queryset()

# 效果:
User.objects.all()          # → SELECT * FROM rbac_users WHERE is_deleted=False
User.objects.with_deleted() # → SELECT * FROM rbac_users (包括已删除的)
```

### 4.5 Model 层 (数据表)

**与 Django 默认 User 的区别**:

| Django 默认 | 本项目 | 原因 |
|------------|--------|------|
| `auth_user` 表 | `rbac_users` 表 | 自定义表名，语义更清晰 |
| `is_staff` (管理后台) | ❌ 不需要 | 不使用 Django Admin |
| `is_superuser` (超管) | ✓ 保留 | 用于权限判断 |
| `password` 字段 | `password_hash` | 显式表明是哈希值 |
| 无软删除 | `is_deleted` | 数据可恢复 |
| 无时间戳 | `created_at`, `updated_at` | 审计追踪 |

### 4.6 Serializer 层 (数据转换)

**职责**：Python Object ⟷ JSON，输入校验

```
需要 3 个 Serializer 而不是 1 个 ModelSerializer 的原因:

┌───────────────────────────────────────────────────────────┐
│  UserCreateSerializer   UserUpdateSerializer   UserOutput │
│  (创建输入)              (更新输入)             (输出)     │
├──────────┬───────────┬─────────────────────┬──────────────┤
│ username │ required  │ optional            │ read_only    │
│ email    │ required  │ optional            │ read_only    │
│ password │ required  │ ❌ (不允许改密码)    │ ❌ (不暴露)   │
│ is_active│ optional  │ optional            │ read_only    │
│ roles    │ ❌         │ ❌                  │ computed     │
│ id       │ ❌         │ ❌                  │ read_only    │
└──────────┴───────────┴─────────────────────┴──────────────┘

关键原则: 输入和输出必须严格分离
  → 输入允许什么字段由 Serializer 控制
  → 输出暴露什么字段由 Serializer 控制
  → 永远不会出现"忘记 exclude password"导致密码泄露
```

### 4.7 异常处理 (Error Reporting)

```
整个项目的错误流:

Service 层抛出:
  raise BusinessError(message='用户名已存在', code='DUPLICATE_USERNAME', status=409)

     ↓ Django 捕获异常

custom_exception_handler() → 转换为 JSON:
  HTTP 409 { "error": { "code": "DUPLICATE_USERNAME", "message": "用户名已存在" } }

     ↓ 前端 Axios 拦截器收到

client.ts 响应拦截器:
  → status 401: 自动跳登录页
  → status 403: 已登录→跳403页; 未登录→忽略
  → 所有错误: 统一格式化为 { code, message, status }
```

---

## 5. 前端分层架构

### 5.1 启动流程

```
main.ts
  │
  ├── ① createApp(App.vue)          Vue 3 应用实例
  ├── ② app.use(ArcoVue)           Arco Design 组件库注册
  ├── ③ app.use(router)            Vue Router 注册
  ├── ④ app.use(store)             Vuex Store 注册
  └── ⑤ app.mount('#app')          挂载到 index.html 的 <div id="app">

App.vue: <router-view /> 根据 URL 渲染对应页面
```

### 5.2 路由守卫 (Router Guard)

```
router.beforeEach((to, from, next) => {
    // 规则: 只要 requiresAuth !== false 就需要登录
    if (to.meta.requiresAuth !== false && !store.getters['user/isAuthenticated']) {
        return next('/login')      // ← 没登录就踢到登录页
    }
    next()                          // ← 放行
})

路由表的权限标记:
  /login          → requiresAuth: false    (未登录可访问)
  /dashboard      → requiresAuth: true     (需要登录)
  /system/users   → requiresAuth: true     (需要登录)
  /403            → requiresAuth: false    (未登录可访问)
  /* (404)        → requiresAuth: false    (未登录可访问)
```

### 5.3 状态管理 (Vuex Store)

```
Store 结构:
  store/
    └── user (namespaced)
        ├── state:       { currentUser, permissions }
        ├── getters:     isAuthenticated → !!currentUser
        ├── mutations:   SET_USER / SET_PERMISSIONS / CLEAR
        └── actions:
            ├── login({username, password})
            │     → POST /api/auth/login/
            │     → commit('SET_USER', res.data)
            │
            ├── fetchUserInfo()
            │     → GET /api/auth/user-info/
            │     → 刷新页面时恢复 session
            │
            └── logout()
                  → POST /api/auth/logout/
                  → commit('CLEAR')

登录流程修正 (之前 403 的根因):
  login action 直接用登录响应的 res.data 设置用户状态
  不再在 login 后调用 fetchUserInfo() ← 这会导致 Cookie 时序问题
```

### 5.4 API 客户端 (Axios)

```
client.ts 核心配置:

const client = axios.create({
    baseURL: '/api',                  // 所有请求前缀 /api
    withCredentials: true,            // 跨域也携带 Cookie
    xsrfCookieName: 'csrftoken',      // CSRFToken Cookie 名
    xsrfHeaderName: 'X-CSRFToken',    // CSRFToken 请求头名
})

client.interceptors.response.use(
    (response) => response.data,      // 成功: 自动解包一层 data
    (error) => {
        // 失败: 统一错误格式
        if (status === 401) → 退出登录
        if (status === 403 && isAuthenticated) → 跳 403 页
        return Promise.reject({ code, message, status })
    }
)
```

### 5.5 Vite 代理 (开发环境)

```
浏览器看到的请求:
  POST http://localhost:5173/api/rbac/users/

Vite Dev Server 做的工作:
  1. 接收请求
  2. 匹配 proxy 规则: /api → http://127.0.0.1:8000
  3. 转发请求到 Django
  4. 把 Django 的响应返回给浏览器

为什么需要代理?
  → 浏览器同源策略: localhost:5173 不能直接向 :8000 发请求
  → 代理让浏览器以为在和同一个服务器通信
  → 生产环境一般用 Nginx 做同样的代理
```

---

## 6. 认证流程 (最核心的安全机制)

### 6.1 登录流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Login   │     │  Vuex    │     │  Django  │     │  MySQL/  │
│  Page    │     │  Store   │     │  Server  │     │  SQLite  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                 │               │                │
     │ ① 用户输入       │               │                │
     │  admin/admin123  │               │                │
     │────────────────→│               │                │
     │                 │               │                │
     │                 │ ② POST /api/auth/login/         │
     │                 │  {username, password}           │
     │                 │──────────────→│                │
     │                 │               │                │
     │                 │               │ ③ UserBackend.authenticate()
     │                 │               │   → User.objects.get(username)
     │                 │               │────────────────→│
     │                 │               │←──── user obj ──│
     │                 │               │                │
     │                 │               │ ④ check_password(raw, hash)
     │                 │               │   bcrypt验证: ✓  │
     │                 │               │                │
     │                 │               │ ⑤ login(request, user)
     │                 │               │   → 生成 sessionid
     │                 │               │   → 写入 django_session 表
     │                 │               │   → Set-Cookie: sessionid=xxx
     │                 │               │   → Set-Cookie: csrftoken=yyy
     │                 │               │                │
     │                 │←── 200 {data: {id, name}} ─────│
     │                 │  + Set-Cookie: sessionid        │
     │                 │  + Set-Cookie: csrftoken        │
     │                 │               │                │
     │                 │ ⑥ commit('SET_USER')            │
     │←─ 登录成功 ─────│               │                │
     │                 │               │                │
     │ ⑦ router.push('/dashboard')                     │
```

### 6.2 后续请求的认证流程

```
每次发请求:
  浏览器自动携带 Cookie:
    Cookie: sessionid=abc123; csrftoken=xyz789
    Header: X-CSRFToken: xyz789

Django 处理:
  ① SessionMiddleware: sessionid → 查 django_session 表 → 反序列化 → request.user
  ② CsrfViewMiddleware: 比较 Cookie.csrftoken === Header.X-CSRFToken → 通过
  ③ DRF IsAuthenticated: request.user 存在 → 放行

双重保护:
  sessionid → 证明"你是谁"(Authentication)
  csrftoken → 证明"这个请求是你发的，不是第三方网站伪造的"(CSRF Protection)
```

---

## 7. 安全机制汇总

| 机制 | 实现 | 防护什么 |
|------|------|---------|
| Session Cookie | `HttpOnly=True` | JS 无法读取，防止 XSS 偷 cookie |
| CSRF Token | 自定义 Header + Cookie 双重校验 | 防止跨站请求伪造 |
| SameSite=Lax | Cookie 属性 | 防止跨站携带 session cookie |
| 密码哈希 | bcrypt (make_password) | 数据库泄露后密码不可逆 |
| 软删除 | is_deleted + BaseManager 自动过滤 | 误删可恢复 |
| 事务保护 | @transaction.atomic | 防止数据不一致 |
| 输入校验 | Serializer 字段级校验 | 防止非法数据入 |
| 输出过滤 | Serializer 只暴露必要字段 | 防止敏感信息泄露 |

---

## 8. 数据库表结构

```
当前已建表:

rbac_users          rbac_roles          rbac_user_roles
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ id (PK)      │    │ id (PK)      │    │ id (PK)      │
│ username     │    │ name         │    │ user_id (FK) ├──→ rbac_users.id
│ email        │    │ code         │    │ role_id (FK) ├──→ rbac_roles.id
│ password_hash│    │ description  │    │ created_at   │
│ is_active    │    │ is_deleted   │    │ updated_at   │
│ is_superuser │    │ created_at   │    │ is_deleted   │
│ last_login_at│    │ updated_at   │    └──────────────┘
│ is_deleted   │    └──────────────┘
│ created_at   │
│ updated_at   │
└──────────────┘

django_session (Django 内置)
┌──────────────┐
│ session_key  │  ← Cookie 中的 sessionid
│ session_data │  ← 加密存储的 user_id 等
│ expire_date  │
└──────────────┘
```

---

## 9. 目录结构速查

```
ram-adminx/
│
├── backend/                     # Django 后端
│   ├── manage.py                # Django CLI 入口
│   ├── requirements.txt         # Python 依赖
│   ├── db.sqlite3               # 开发数据库
│   ├── config/                  # 项目配置
│   │   ├── settings/
│   │   │   ├── base.py          # 公共配置 (中间件、DRF、认证等)
│   │   │   └── dev.py           # 开发环境覆盖 (DEBUG、ALLOWED_HOSTS)
│   │   └── urls.py              # 根路由
│   └── apps/                    # 业务模块
│       ├── common/              # 共享基础设施
│       │   ├── base_model.py    # 抽象基类 (时间戳+软删除)
│       │   ├── managers.py      # BaseManager (自动过滤已删除)
│       │   └── exceptions.py    # BusinessError + DRF 错误处理器
│       ├── rbac/                # 权限管理模块
│       │   ├── models.py        # User, Role, UserRole 模型
│       │   ├── backends.py      # 自定义认证后端
│       │   ├── services/        # 业务逻辑层
│       │   │   └── user_service.py
│       │   ├── serializers/     # 数据序列化
│       │   │   └── user_serializers.py
│       │   ├── views/           # HTTP 接口
│       │   │   ├── auth_views.py
│       │   │   └── user_views.py
│       │   ├── urls_auth.py     # 认证路由
│       │   └── urls_user.py     # 用户管理路由
│       └── audit/               # 审计模块 (预留)
│
├── frontend/                    # Vue 3 前端
│   ├── vite.config.ts           # Vite 配置 (代理、别名、分包)
│   ├── index.html               # HTML 入口
│   └── src/
│       ├── main.ts              # Vue 应用启动
│       ├── App.vue              # 根组件 (router-view)
│       ├── router/
│       │   └── index.ts         # 路由表 + 路由守卫
│       ├── stores/
│       │   ├── index.ts         # Vuex Store 创建
│       │   └── user.ts          # 用户模块 (auth 状态管理)
│       ├── api/
│       │   ├── client.ts        # Axios 实例 + 拦截器
│       │   └── modules/
│       │       ├── auth.ts      # 认证 API
│       │       └── user.ts      # 用户管理 API
│       ├── types/
│       │   └── user.ts          # TypeScript 类型定义
│       ├── layouts/
│       │   └── MainLayout.vue   # 主布局 (侧边栏+头部+内容区)
│       └── views/
│           ├── login/           # 登录页
│           ├── dashboard/       # 仪表盘
│           ├── error/           # 403/404 错误页
│           └── system/user/     # 用户管理
│               ├── UserListView.vue
│               └── UserFormDialog.vue
│
└── ARCHITECTURE.md              # ← 本文件
```

---

## 10. 开发命令

```bash
# ── 后端 ──
cd backend
venv\Scripts\activate            # 激活虚拟环境
python manage.py runserver       # 启动 Django (8000)
python manage.py makemigrations  # 生成迁移文件
python manage.py migrate         # 执行迁移
python manage.py init_rbac       # 初始化 admin 用户

# ── 前端 ──
cd frontend
npm install                      # 安装依赖
npm run dev                      # 启动 Vite (5173)
npm run build                    # 生产构建
```

---

**架构核心要点**:

1. **分层解耦** — ViewSet → Service → Manager → Model，每层只做一件事
2. **输入输出分离** — Create/Update/Output 三个 Serializer，绝不混用
3. **错误统一** — BusinessError → custom_exception_handler → `{error: {code, message}}`
4. **安全第一** — Session + CSRF 双重保护，密码 bcrypt 哈希，软删除防误删
5. **前端透明代理** — 开发时 Vite 代理 /api → Django，生产用 Nginx
