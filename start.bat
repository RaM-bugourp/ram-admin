@echo off
chcp 65001 >nul
REM ===========================================
REM ram-admin 一键启动脚本 (Windows)
REM ===========================================

echo 🚀 启动 ram-admin 开发环境...

REM 检查 Python
where py >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Python，请先安装
    pause
    exit /b 1
)

REM 检查 Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Node.js，请先安装
    pause
    exit /b 1
)

REM 后端设置
echo 📦 设置后端环境...
cd backend

REM 创建虚拟环境
if not exist "venv" (
    echo 创建 Python 虚拟环境...
    py -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装 Python 依赖...
pip install -r requirements.txt

REM 数据库迁移
echo 执行数据库迁移...
py manage.py migrate --run-syncdb 2>nul || py manage.py migrate

REM 创建超级用户
echo 检查超级用户...
py -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ram_admin.settings'); import django; django.setup(); from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123'); print('✅ 超级用户: admin / admin123')"

REM 启动后端（新窗口）
echo 🔥 启动后端服务...
start "ram-admin-backend" cmd /k "venv\Scripts\activate.bat && py manage.py runserver 0.0.0.0:8000"

REM 前端设置
echo 📦 设置前端环境...
cd ..\frontend

REM 安装依赖
if not exist "node_modules" (
    echo 安装 Node.js 依赖...
    call npm install
)

REM 启动前端（新窗口）
echo 🔥 启动前端服务...
start "ram-admin-frontend" cmd /k "npm run dev"

echo.
echo ✅ 启动完成！
echo    前端: http://localhost:5173
echo    后端: http://localhost:8000
echo    账号: admin / admin123
echo.
echo 按任意键退出此窗口（服务将继续运行）...
pause >nul
