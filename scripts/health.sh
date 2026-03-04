#!/bin/bash
# Edge TTS Service 健康检查脚本

# 默认配置
SERVICE_PORT=${SERVICE_PORT:-8000}
SERVICE_HOST=${SERVICE_HOST:-localhost}

echo "🔍 检查 Edge TTS Service 健康状态..."
echo ""

# 检查服务是否响应
response=$(curl -s -o /dev/null -w "%{http_code}" http://$SERVICE_HOST:$SERVICE_PORT/health 2>/dev/null || echo "000")

if [ "$response" = "200" ]; then
    echo "✅ 服务运行正常"

    # 显示详细状态
    echo ""
    curl -s http://$SERVICE_HOST:$SERVICE_PORT/health | python3 -m json.tool 2>/dev/null || curl -s http://$SERVICE_HOST:$SERVICE_PORT/health
    exit 0
else
    echo "❌ 服务未响应 (HTTP $response)"
    echo ""
    echo "💡 请检查:"
    echo "  1. 服务是否已启动 (bash scripts/start.sh)"
    echo "  2. 端口 $SERVICE_PORT 是否被占用"
    echo "  3. 防火墙设置"
    exit 1
fi
