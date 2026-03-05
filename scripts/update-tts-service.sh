#!/bin/bash
# 更新 TTS 服务 - 添加 Opus 格式支持

set -e

echo "🚀 更新 Edge TTS Service（添加 Opus 支持）..."

# 1. 安装 ffmpeg（用于 MP3 转 Opus）
echo "📦 安装 ffmpeg..."
apt install -y ffmpeg

# 2. 备份旧版本
echo "💾 备份旧版本..."
cd /opt/edge-tts-service
if [ -d "app_backup" ]; then
    rm -rf app_backup
fi
cp -r app app_backup

# 3. 停止服务
echo "🛑 停止服务..."
systemctl stop edge-tts-service

# 4. 更新代码（从上传的新文件）
echo "📝 更新代码..."
# 您需要先上传新的代码文件，然后这里会自动替换

# 5. 更新依赖
echo "📦 更新依赖..."
source venv/bin/activate
pip install aiofiles

# 6. 创建静态文件目录
echo "📁 创建静态文件目录..."
mkdir -p /tmp/tts_audio

# 7. 重启服务
echo "🚀 启动服务..."
systemctl start edge-tts-service

# 8. 等待启动
sleep 3

# 9. 测试服务
echo "🧪 测试服务..."
echo ""
echo "测试 1: 健康检查"
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "测试 2: 生成 Opus 格式音频"
curl -s -X POST http://localhost:8000/tts/feishu \
  -H "Content-Type: application/json" \
  -d '{"text":"测试Opus音频"}' | python3 -m json.tool

echo ""
echo "✅ 更新完成！"
echo ""
echo "📊 新增功能:"
echo "  - POST /tts/feishu - 飞书专用接口（返回 Opus + URL）"
echo "  - POST /tts/url  - 返回音频 URL"
echo "  - 参数 format=opus - 支持 Opus 格式"
echo ""
echo "📁 静态文件存储: /tmp/tts_audio/"
echo "🌐 访问地址: http://115.190.252.250:8000/static/audio/"
