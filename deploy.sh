#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════
# ram-adminx 一键部署脚本
# 用法: bash deploy.sh [init|start|stop|restart|logs|migrate|collectstatic]
# ══════════════════════════════════════════════════════════

set -euo pipefail

COMPOSE="docker compose"

case "${1:-help}" in
    init)
        echo "==> 初始化部署环境..."
        if [ ! -f .env ]; then
            cp .env.example .env
            echo "    已创建 .env，请编辑后重新运行"
            echo "    必须修改: POSTGRES_PASSWORD, DJANGO_SECRET_KEY, AI_AGENT_TOKEN_SECRET"
            exit 0
        fi
        $COMPOSE build
        $COMPOSE up -d db redis
        echo "    等待数据库就绪..."
        sleep 5
        $COMPOSE exec backend python manage.py migrate --noinput
        $COMPOSE exec backend python manage.py createsuperuser --noinput || true
        echo "==> 初始化完成! 运行 bash deploy.sh start 启动服务"
        ;;

    start)
        echo "==> 启动所有服务..."
        $COMPOSE up -d
        echo "==> 服务已启动"
        echo "    前端: http://localhost"
        echo "    后端: http://localhost:8000/admin/"
        ;;

    stop)
        echo "==> 停止所有服务..."
        $COMPOSE down
        ;;

    restart)
        echo "==> 重启服务..."
        $COMPOSE restart
        ;;

    migrate)
        echo "==> 执行数据库迁移..."
        $COMPOSE exec backend python manage.py migrate --noinput
        ;;

    collectstatic)
        echo "==> 收集静态文件..."
        $COMPOSE exec backend python manage.py collectstatic --noinput
        ;;

    logs)
        $COMPOSE logs -f --tail=100
        ;;

    test)
        echo "==> 运行后端测试..."
        $COMPOSE exec backend pytest apps/ -v --tb=short -p no:cacheprovider
        ;;

    help|*)
        echo "ram-adminx 部署脚本"
        echo ""
        echo "用法: bash deploy.sh <命令>"
        echo ""
        echo "命令:"
        echo "  init          初始化部署环境（首次部署）"
        echo "  start         启动所有服务"
        echo "  stop          停止所有服务"
        echo "  restart       重启所有服务"
        echo "  migrate       执行数据库迁移"
        echo "  collectstatic 收集静态文件"
        echo "  logs          查看实时日志"
        echo "  test          运行测试"
        ;;
esac
