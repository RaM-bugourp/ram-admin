# RaM Admin 部署指南

---

## 一、开发环境

### 1.1 系统要求

- Python 3.12+
- Node.js 22+
- SQLite（开发）/ PostgreSQL 16+（生产）

### 1.2 快速启动

**Windows**:
```bash
# 双击运行
start.bat

# 或命令行
python -m venv backend\venv
backend\venv\Scripts\activate
pip install -r backend\requirements.txt
python backend\manage.py migrate
python backend\manage.py runserver

cd frontend
npm install
npm run dev
```

**Linux/macOS**:
```bash
# 一键启动
./start.sh

# 或手动启动
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py runserver

cd frontend
npm install
npm run dev
```

### 1.3 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 | http://localhost:8000 |
| API 文档 | http://localhost:8000/api/docs/ |
| Django Admin | http://localhost:8000/admin/ |

### 1.4 默认账号

- 用户名: `admin`
- 密码: `admin123`

---

## 二、生产部署

### 2.1 Docker 部署（推荐）

#### 步骤 1：准备环境配置

```bash
cp .env.example .env
# 编辑 .env 修改生产配置
```

#### 步骤 2：构建并启动

```bash
docker-compose up -d --build
```

#### 步骤 3：初始化数据

```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

### 2.2 传统部署

#### 后端部署

```bash
# 1. 安装依赖
pip install -r requirements.txt
pip install gunicorn

# 2. 收集静态文件
python manage.py collectstatic --noinput

# 3. 数据库迁移
python manage.py migrate

# 4. 启动 Gunicorn
gunicorn ram_admin.wsgi:application \
  -b 0.0.0.0:8000 \
  -w 4 \
  --access-logfile - \
  --error-logfile -
```

#### Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 静态文件
    location /static {
        proxy_pass http://127.0.0.1:8000;
    }

    # 媒体文件
    location /media {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

#### 前端部署

```bash
cd frontend
npm install
npm run build

# dist 目录部署到 Nginx 或 CDN
```

### 2.3 PostgreSQL 配置

```bash
# 安装 PostgreSQL
sudo apt install postgresql postgresql-contrib

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE ram_admin;
CREATE USER ram_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ram_admin TO ram_user;
```

修改 `.env`:
```env
DJANGO_DB_ENGINE=django.db.backends.postgresql
DJANGO_DB_NAME=ram_admin
DJANGO_DB_USER=ram_user
DJANGO_DB_PASSWORD=your_password
DJANGO_DB_HOST=localhost
DJANGO_DB_PORT=5432
```

---

## 三、性能优化

### 3.1 数据库优化

```python
# settings.py

# 连接池（生产环境）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'
        }
    }
}
```

### 3.2 缓存配置

```python
# settings.py

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
    }
}
```

### 3.3 静态文件 CDN

```python
# settings.py

# 使用 WhiteNoise 直接服务静态文件
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

## 四、安全配置

### 4.1 生产环境检查清单

```bash
# Django 安全检查
python manage.py check --deploy
```

### 4.2 关键配置

```python
# settings.py

DEBUG = False

ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# 其他
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

### 4.3 密钥管理

```python
# 从环境变量读取
import os
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
```

---

## 五、监控与日志

### 5.1 日志配置

```python
# settings.py

LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/ram-admin/app.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

### 5.2 健康检查

```bash
# 添加到监控脚本
curl -f http://localhost:8000/health/ || exit 1
```

---

## 六、备份策略

### 6.1 数据库备份

```bash
# PostgreSQL 备份
pg_dump -U ram_user ram_admin > backup_$(date +%Y%m%d).sql

# 恢复
psql -U ram_user ram_admin < backup_20260420.sql
```

### 6.2 媒体文件备份

```bash
# 备份上传文件
tar -czf media_$(date +%Y%m%d).tar.gz backend/media/
```

---

## 七、常见问题

### Q1: 端口被占用

```bash
# 查看端口占用
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/macOS

# 杀死进程
kill -9 <PID>
```

### Q2: 数据库连接失败

检查：
1. PostgreSQL 服务是否启动
2. `.env` 配置是否正确
3. 防火墙是否放行

### Q3: 静态文件 404

```bash
# 重新收集静态文件
python manage.py collectstatic --noinput
```

### Q4: 权限问题

```bash
# Linux 文件权限
chmod -R 755 backend/staticfiles/
chmod -R 755 backend/media/
```
