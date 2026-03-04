#!/bin/bash
# 火山引擎服务器部署脚本
# 在服务器上手动执行此脚本

set -e

echo "🚀 开始部署 Edge TTS Service..."
echo ""

# 1. 更新系统
echo "📦 更新系统..."
apt update && apt upgrade -y

# 2. 安装必要工具
echo "🔧 安装必要工具..."
apt install -y python3 python3-pip python3-venv git curl

# 3. 创建应用目录
echo "📁 创建应用目录..."
mkdir -p /opt/edge-tts-service
cd /opt/edge-tts-service

# 4. 解压项目文件
echo "📦 解压项目文件..."
if [ -f ~/edge-tts-skill.tar.gz ]; then
    tar -xzf ~/edge-tts-skill.tar.gz --strip-components=1
    echo "✅ 项目文件解压完成"
else
    echo "❌ 找不到上传的文件: ~/edge-tts-skill.tar.gz"
    echo "请先执行: scp edge-tts-skill.tar.gz root@115.190.252.250:/root/"
    exit 1
fi

# 5. 创建虚拟环境
echo "🐍 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 6. 安装依赖
echo "📦 安装 Python 依赖..."
pip install --upgrade pip
NO_PROXY="*" pip install -r requirements.txt

# 7. 创建 systemd 服务
echo "🔧 创建系统服务..."
cat > /etc/systemd/system/edge-tts-service.service <<'EOF'
[Unit]
Description=Edge TTS Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/edge-tts-service
Environment="PATH=/opt/edge-tts-service/venv/bin:/usr/local/bin"
ExecStart=/opt/edge-tts-service/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 8. 配置防火墙
echo "🔒 配置防火墙..."
ufw allow 8000/tcp 2>/dev/null || echo "防火墙未启用或已配置"

# 9. 启动服务
echo "🚀 启动服务..."
systemctl daemon-reload
systemctl enable edge-tts-service
systemctl start edge-tts-service

# 10. 等待服务启动并检查状态
echo "⏳ 等待服务启动..."
sleep 5
systemctl status edge-tts-service --no-pager

# 11. 测试服务
echo ""
echo "🧪 测试服务..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "服务可能未正常启动"

echo ""
echo "========================================="
echo "   部署完成！"
echo "========================================="
echo ""
echo "📊 服务地址:"
echo "   API 文档: http://115.190.252.250:8000/docs"
echo "   健康检查: http://115.190.252.250:8000/health"
echo "   服务地址: http://115.190.252.250:8000/tts"
echo ""
echo "🔧 管理命令:"
echo "   状态: sudo systemctl status edge-tts-service"
echo "   日志: sudo journalctl -u edge-tts-service -f"
echo "   重启: sudo systemctl restart edge-tts-service"
echo ""
echo "⚠️  下一步:"
echo "   1. 在火山引擎控制台配置安全组，开放 8000 端口"
echo "   2. 在本地测试: curl http://115.190.252.250:8000/health"
echo ""
