# 配置清单 — Configuration Reference

> 记录前后端所有配置项、环境变量及生产环境注意事项。
> 
> 最后更新: 2026-06-09

---

## 1. 后端配置（Django）

配置文件位于 `backend/config/settings/`，采用 **base.py + dev.py** 分层结构。

### 1.1 基础配置 (`base.py`)

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| `SECRET_KEY` | 环境变量 `DJANGO_SECRET_KEY`，fallback 为开发密钥 | **生产必须更换** |
| `DEBUG` | `False` | 生产环境必须为 False |
| `ALLOWED_HOSTS` | `[]`（空，由 dev.py 覆盖） | 生产需填写域名/IP |
| `BASE_DIR` | 自动推导（`settings/` 向上三级） | — |

### 1.2 数据库 (`dev.py`)

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| `ENGINE` | `django.db.backends.sqlite3` | 开发用 SQLite；生产建议 PostgreSQL |
| `NAME` | `BASE_DIR / 'db.sqlite3'` | SQLite 文件路径 |

> ⚠️ 生产环境建议更换为 PostgreSQL：
> ```python
> DATABASES = {
>     'default': {
>         'ENGINE': 'django.db.backends.postgresql',
>         'NAME': os.environ.get('DB_NAME'),
>         'USER': os.environ.get('DB_USER'),
>         'PASSWORD': os.environ.get('DB_PASSWORD'),
>         'HOST': os.environ.get('DB_HOST', 'localhost'),
>         'PORT': os.environ.get('DB_PORT', '5432'),
>     }
> }
> ```

### 1.3 认证 & Session

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `AUTH_USER_MODEL` | `'rbac.User'` | 自定义 User 模型 |
| `AUTHENTICATION_BACKENDS` | `['apps.rbac.backends.UserBackend']` | 自定义后端（过滤软删除） |
| `SESSION_COOKIE_HTTPONLY` | `True` | 防 XSS 读取 Cookie |
| `SESSION_COOKIE_SAMESITE` | `'Lax'` | CSRF 基础防护 |
| `CSRF_COOKIE_HTTPONLY` | `False` | 允许 JS 读取 CSRF Token |
| `CSRF_COOKIE_SAMESITE` | `'Lax'` | — |

### 1.4 DRF 配置

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [SessionAuthentication],
    'DEFAULT_PERMISSION_CLASSES':     [IsAuthenticated],
    'DEFAULT_PAGINATION_CLASS':       PageNumberPagination,
    'PAGE_SIZE':                       20,
    'DEFAULT_FILTER_BACKENDS':        [DjangoFilterBackend, SearchFilter, OrderingFilter],
    'EXCEPTION_HANDLER':              'apps.common.exceptions.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES':      [JSONRenderer],
}
```

### 1.5 中间件顺序（关键）

```
1. CorsMiddleware          ← 必须最前
2. SecurityMiddleware
3. SessionMiddleware
4. CommonMiddleware
5. CsrfViewMiddleware     ← Session 之后
6. AuthenticationMiddleware
7. MessageMiddleware
8. XFrameOptionsMiddleware
```

> ⚠️ `CorsMiddleware` 必须在最前面，否则 CORS 头部不生效。

### 1.6 CORS 配置

| 配置项 | dev.py | base.py（生产） |
|--------|--------|----------------|
| `CORS_ALLOW_ALL_ORIGINS` | `True` | — |
| `CORS_ALLOW_CREDENTIALS` | `True` | `True` |
| `CORS_ALLOWED_ORIGINS` | `[]` | **需填写前端域名** |
| `CSRF_TRUSTED_ORIGINS` | `['http://localhost:5173']` | **需填写前端 HTTPS 域名** |

> ⚠️ 生产环境 `CORS_ALLOW_ALL_ORIGINS` 必须改为 `False`，并在 `CORS_ALLOWED_ORIGINS` 中精确填写允许的域名。

---

## 2. 前端配置（Vite + Vue 3）

### 2.1 Vite (`vite.config.ts`)

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `server.port` | `5173` | 开发服务器端口 |
| `server.proxy['/api']` | `http://127.0.0.1:8000` | API 代理，避免 CORS |
| `build.rollupOptions.manualChunks` | `vendor` / `arcoDesign` | 分包策略 |
| `build.chunkSizeWarningLimit` | `500` KB | 超过此值报警告 |

### 2.2 环境变量

前端通过 `import.meta.env` 读取环境变量，需创建 `.env.development` / `.env.production`。

目前**未配置**，建议补充：

```bash
# .env.development
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_APP_TITLE=ram-adminx 管理系统

# .env.production
VITE_API_BASE_URL=/api
VITE_APP_TITLE=ram-adminx 管理系统
```

> 然后修改 `api/client.ts` 中的 `baseURL`：
> ```ts
> baseURL: import.meta.env.VITE_API_BASE_URL || '/api'
> ```

### 2.3 TypeScript

`tsconfig.json` 关键配置：

| 配置项 | 值 |
|--------|-----|
| `compilerOptions.paths['@/*']` | `['src/*']` |
| `compilerOptions.strict` | `true` |
| `compilerOptions.noUnusedLocals` | `true` |

---

## 3. 环境变量清单（`.env`）

建议在 `backend/` 目录下创建 `.env` 文件（已被 `.gitignore` 排除），生产环境通过宿主环境变量注入。

```bash
# Django
DJANGO_SECRET_KEY=xxx              # 生产必须更换
DJANGO_SETTINGS_MODULE=config.settings.prod   # 生产用 prod.py
DJANGO_DEBUG=False

# 数据库（PostgreSQL）
DB_NAME=ram_adminx
DB_USER=ram_adminx
DB_PASSWORD=xxx
DB_HOST=localhost
DB_PORT=5432

# Redis（可选，用于 Session/Cache）
REDIS_URL=redis://localhost:6379/0

# 邮件（可选）
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=xxx
```

---

## 4. 生产环境 Checklist

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` 更换为强随机值（≥50 字符）
- [ ] `ALLOWED_HOSTS` 填写正确域名
- [ ] 数据库更换为 PostgreSQL
- [ ] `CORS_ALLOW_ALL_ORIGINS = False`，精确填写 `CORS_ALLOWED_ORIGINS`
- [ ] `CSRF_TRUSTED_ORIGINS` 填写前端 HTTPS 域名
- [ ] 配置 HTTPS（SSL/TLS），设置 `SESSION_COOKIE_SECURE = True`、`CSRF_COOKIE_SECURE = True`
- [ ] 静态文件收集 `python manage.py collectstatic`，由 Nginx/CDN 托管
- [ ] 日志接入外部服务（Sentry / ELK）
- [ ] 添加 Rate Limiting（DRF Throttling 或 django-ratelimit）
- [ ] `.env` 文件权限设置为 600，不被 Git 追踪

---

## 5. 端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端（Vite dev server） | `5173` | `npm run dev` |
| 后端（Django runserver） | `8000` | `python manage.py runserver 8000` |
| 前端（生产 build） | 由 Nginx 托管 | `npm run build` → `dist/` |

---

## 6. 启动命令速查

### 后端

```bash
cd backend

# 开发
python manage.py runserver 8000

# 数据库迁移
python manage.py migrate

# 初始化角色
python manage.py init_rbac

# 生产（Gunicorn 示例）
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 开发
npm run dev

# 生产构建
npm run build

# 预览生产构建
npm run preview
```
