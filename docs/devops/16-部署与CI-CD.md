# 16 - 部署与 CI/CD

## 适用场景
前后端开发完成后，配置容器化部署和自动化流水线。

## 关联原则
- 原则6：最小权限 — 数据库账户/API Key 按环境隔离
- 原则9：强制审查 — CI/CD 中集成自动化检查
- 原则8：测试 — 流水线中自动运行测试

## 核心规则
1. **Docker Compose 一键启动全部服务**
2. **环境变量通过 `.env` 管理（不提交到 git）**
3. **CI/CD 包含：lint → test → security scan → build**
4. **数据库密码用 secrets，不硬编码**

## 开发步骤

### 步骤 1：Docker Compose

文件：`docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${DB_NAME:-django_vue_adminx}
      POSTGRES_USER: ${DB_USER:-app_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-change_me}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-app_user}"]
      interval: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  backend:
    build: ./backend
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4"
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.prod
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: ${DB_NAME}
      DB_USER: ${DB_USER}
      DB_PASSWORD: ${DB_PASSWORD}
      REDIS_URL: redis://redis:6379/0
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY}
      ALLOWED_HOSTS: ${ALLOWED_HOSTS:-localhost}
      CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:3000}
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/static
      - media_volume:/media

volumes:
  pgdata:
  static_volume:
  media_volume:
```

### 步骤 2：Nginx 配置

文件：`deploy/nginx.conf`

```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name admin.company.com;

    # 静态文件直接由 Nginx 服务
    location /static/ {
        alias /static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /media/;
        expires 7d;
    }

    # API 请求反代到 Django
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
    }

    # 前端静态文件
    location / {
        root /frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

### 步骤 3：Dockerfile（后端）

文件：`backend/Dockerfile`

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
```

### 步骤 4：环境变量模板

文件：`.env.example`

```bash
# 数据库
DB_NAME=django_vue_adminx
DB_USER=app_user
DB_PASSWORD=change_me_to_random_string

# Django
DJANGO_SECRET_KEY=change_me_to_random_50_char_string
DJANGO_SETTINGS_MODULE=config.settings.prod

# 部署
ALLOWED_HOSTS=admin.company.com,api.company.com
CORS_ORIGINS=https://admin.company.com

# Redis
REDIS_URL=redis://redis:6379/0
```

### 步骤 5：CI/CD 流水线

文件：`.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.13' }
      - run: pip install ruff
      - run: ruff check backend/

  test-backend:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r backend/requirements.txt
      - run: |
          cd backend
          DJANGO_SETTINGS_MODULE=config.settings.test pytest tests/ --cov=apps --cov-fail-under=75
        env:
          DB_HOST: localhost
          DB_NAME: test
          DB_USER: test
          DB_PASSWORD: test

  security-scan:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install bandit safety
      - run: bandit -r backend/ -ll
      - run: safety check -r backend/requirements.txt --ignore=70612

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: |
          cd front-end
          npm ci
          npm run type-check
          npm run lint
          npm run test -- --coverage

  build:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend, security-scan]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build
```

### 步骤 6：pre-commit 钩子

文件：`.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.0.0
    hooks:
      - id: eslint
        files: \.(ts|vue)$
        args: [--fix]
```

### 步骤 7：数据库迁移策略

**零停机迁移原则**：

| 操作 | 安全？ | 说明 |
|------|--------|------|
| 新增表 | ✅ | 直接 migrate，对现有流量无影响 |
| 新增字段（含默认值） | ✅ | Django 5.x 支持 `db_default`，无需锁表 |
| 新增非空字段（无默认值） | ❌ | 需要分步：①加nullable字段 ②数据回填 ③改为NOT NULL |
| 删除字段 | ⚠️ | 分三步：①代码不读该字段 ②migrate删除 ③确认无回滚需求 |
| 重命名字段 | ❌ | 用新增+数据同步+删除三步替代 |
| 修改字段类型 | ❌ | 新建列+数据迁移+切换+删除旧列 |
| 添加索引 | ⚠️ | 大表用 `CONCURRENTLY`（PostgreSQL），Django 需手写 migration |

**数据回填模板**：

```python
# apps/rbac/migrations/0003_backfill_department.py
from django.db import migrations

def backfill_department(apps, schema_editor):
    User = apps.get_model('rbac', 'User')
    Department = apps.get_model('rbac', 'Department')
    default_dept = Department.objects.filter(code='default').first()
    if default_dept:
        User.objects.filter(department__isnull=True).update(department=default_dept)

class Migration(migrations.Migration):
    dependencies = [('rbac', '0002_add_department_field')]
    operations = [
        migrations.RunPython(backfill_department, migrations.RunPython.noop),
    ]
```

**迁移安全检查**：
```bash
# 部署前检查迁移是否安全
python manage.py makemigrations --check --dry-run
python manage.py sqlmigrate rbac 0003  # 预览SQL，确认无锁表操作
```

### 步骤 8：部署检查清单

| 检查项 | 命令 |
|--------|------|
| 后端健康检查 | `curl http://localhost:8000/api/health/` |
| 静态文件可访问 | `curl http://localhost/static/admin/css/base.css` |
| 数据库可连接 | `docker compose exec backend python manage.py showmigrations` |
| 前端可访问 | `curl http://localhost/` |
| API 可调用 | `curl http://localhost/api/users/ -H "Authorization: Bearer xxx"` |

## 反模式（禁止）
- ❌ `docker-compose.yml` 中硬编码密码
- ❌ CI/CD 跳过测试直接构建
- ❌ 用 `latest` tag（应固定版本号）
- ❌ 数据库不配 volume（数据会丢失）

## 自检清单
- [ ] docker-compose.yml 无硬编码密码（用 `${VAR}`）？
- [ ] `.env` 已加入 `.gitignore`？
- [ ] 生产环境 `DEBUG=False`？
- [ ] CI/CD 包含 lint → test → security scan → build？
- [ ] Docker 镜像版本号固定（不用 `latest`）？
- [ ] 数据库有 volume 持久化？
- [ ] 健康检查配置了？
