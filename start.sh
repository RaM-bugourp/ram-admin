#!/bin/bash
# ===========================================
# ram-admin 一键启动脚本 (Linux/macOS)
# ===========================================

set -e

echo "🚀 启动 ram-admin 开发环境..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请先安装"
    exit 1
fi

# 后端设置
echo "📦 设置后端环境..."
cd backend

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装 Python 依赖..."
pip install -r requirements.txt

# 数据库迁移
echo "执行数据库迁移..."
python manage.py migrate --run-syncdb 2>/dev/null || python manage.py migrate

# 创建超级用户（如果不存在）
echo "检查超级用户..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ram_admin.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ 创建超级用户: admin / admin123')
else:
    print('✅ 超级用户已存在')
"

# 启动后端（后台）
echo "🔥 启动后端服务..."
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

# 前端设置
echo "📦 设置前端环境..."
cd ../frontend

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "安装 Node.js 依赖..."
    npm install
fi

# 启动前端
echo "🔥 启动前端服务..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 启动完成！"
echo "   前端: http://localhost:5173"
echo "   后端: http://localhost:8000"
echo "   账号: admin / admin123"
echo ""
echo "按 Ctrl+C 停止服务..."

# 等待子进程
wait $BACKEND_PID $FRONTEND_PID
