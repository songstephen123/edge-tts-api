#!/bin/bash
# Edge TTS Service 启动脚本

set -e

# 加载 .env 文件（如果存在）
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 默认配置
SERVICE_PORT=${SERVICE_PORT:-8000}
SERVICE_HOST=${SERVICE_HOST:-0.0.0.0}
LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "🚀 启动 Edge TTS Service..."
echo "=============================="
echo "🌐 服务地址: http://$SERVICE_HOST:$SERVICE_PORT"
echo "📖 API 文档: http://localhost:$SERVICE_PORT/docs"
echo "🔍 健康检查: http://localhost:$SERVICE_PORT/health"
echo ""

# 检查是否在虚拟环境中
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "✅ 虚拟环境: $VIRTUAL_ENV"
fi

# 启动服务
uvicorn app.main:app \
    --host $SERVICE_HOST \
    --port $SERVICE_PORT \
    --log-level $LOG_LEVEL
