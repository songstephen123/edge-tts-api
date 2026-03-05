#!/bin/bash
# 一键更新部署脚本 - Opus 优化版

set -e

echo "🚀 部署 Opus 优化版本（opusenc + 流式处理 + 缓存）"
echo "============================================"

# 1. 安装 opusenc
echo ""
echo "📦 步骤 1/5: 安装 opusenc..."
if command -v opusenc &> /dev/null; then
    echo "✅ opusenc 已安装"
else
    apt update
    apt install -y opus-tools
    echo "✅ opusenc 安装完成"
fi

# 2. 创建缓存目录
echo ""
echo "📁 步骤 2/5: 创建缓存目录..."
mkdir -p /tmp/tts_cache
chmod 755 /tmp/tts_cache
echo "✅ 缓存目录已创建"

# 3. 停止服务
echo ""
echo "🛑 步骤 3/5: 停止服务..."
systemctl stop edge-tts-service 2>/dev/null || echo "服务未运行"

# 4. 更新代码（需要先上传文件）
echo ""
echo "📝 步骤 4/5: 更新代码文件..."
echo "请先上传以下文件到服务器："
echo "  - app/routes/tts.py"
echo "  - app/services/opus_converter.py"
echo "  - requirements.txt"
echo ""
read -p "文件上传完成后按 Enter 继续..."

# 5. 更新依赖
echo ""
echo "📦 步骤 5/5: 更新依赖..."
cd /opt/edge-tts-service
source venv/bin/activate

# 安装新依赖
pip install aiofiles --upgrade

# 检查是否需要 opus-tools
if ! command -v opusenc &> /dev/null; then
    echo "⚠️  opusenc 未安装，安装中..."
    apt install -y opus-tools
fi

# 6. 重启服务
echo ""
echo "🚀 启动服务..."
systemctl start edge-tts-service

# 7. 等待启动
sleep 3

# 8. 检查状态
echo ""
echo "📊 服务状态:"
systemctl status edge-tts-service --no-pager

# 9. 测试服务
echo ""
echo "🧪 测试服务..."
echo "健康检查:"
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "性能测试（3次 Opus 转换）:"
for i in {1..3}; do
    echo "测试 $i:"
    time curl -s -X POST http://localhost:8000/tts/feishu \
      -H "Content-Type: application/json" \
      -d '{"text":"性能测试"}' \
      | python3 -m json.tool | grep -E "(duration|cached)"
    echo ""
done

echo ""
echo "============================================"
echo "   部署完成！"
echo "============================================"
echo ""
echo "📊 性能监控:"
echo "   curl http://localhost:8000/tts/performance"
echo ""
echo "📁 缓存目录:"
echo "   /tmp/tts_cache/"
echo ""
echo "🔧 管理命令:"
echo "   systemctl status edge-tts-service"
echo "   journalctl -u edge-tts-service -f"
echo ""
