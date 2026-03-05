#!/bin/bash
# 飞书集成服务部署脚本

set -e

echo "🚀 部署飞书 TTS 集成服务..."

# 配置
SERVICE_DIR="/opt/feishu-tts-integration"
SERVICE_PORT=8001

# 创建目录
echo "📁 创建服务目录..."
mkdir -p $SERVICE_DIR
cd $SERVICE_DIR

# 复制服务文件
echo "📦 复制服务文件..."
cp ~/edge-tts-skill/feishu_integration_service.py $SERVICE_DIR/
cp ~/edge-tts-skill/feishu.env.example $SERVICE_DIR/feishu.env

# 创建虚拟环境
echo "🐍 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install fastapi uvicorn requests

# 配置环境变量
echo "⚙️  配置环境变量..."
if [ ! -f feishu.env ]; then
    cp feishu.env.example feishu.env
    echo ""
    echo "⚠️  请编辑配置文件："
    echo "   vim $SERVICE_DIR/feishu.env"
    echo ""
    echo "填入您的飞书应用信息："
    echo "   - FEISHI_APP_ID"
    echo "   - FEISHI_APP_SECRET"
    echo ""
    read -p "配置完成后按 Enter 继续..."
fi

# 创建 systemd 服务
echo "🔧 创建系统服务..."
cat > /etc/systemd/system/feishu-tts-integration.service <<EOF
[Unit]
Description=Feishu TTS Integration Service
After=network.target edge-tts-service.service

[Service]
Type=simple
User=root
WorkingDirectory=$SERVICE_DIR
Environment="PATH=$SERVICE_DIR/venv/bin"
EnvironmentFile=$SERVICE_DIR/feishu.env
ExecStart=$SERVICE_DIR/venv/bin/uvicorn feishu_integration_service:app --host 0.0.0.0 --port $SERVICE_PORT
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 配置防火墙
echo "🔒 配置防火墙..."
ufw allow $SERVICE_PORT/tcp 2>/dev/null || echo "防火墙未启用"

# 启动服务
echo "🚀 启动服务..."
systemctl daemon-reload
systemctl enable feishu-tts-integration
systemctl start feishu-tts-integration

# 检查状态
sleep 3
echo ""
echo "📊 服务状态:"
systemctl status feishu-tts-integration --no-pager

# 显示信息
echo ""
echo "========================================="
echo "   部署完成！"
echo "========================================="
echo ""
echo "🌐 服务地址:"
echo "   http://YOUR_SERVER_IP:$SERVICE_PORT"
echo ""
echo "📝 飞书事件订阅地址:"
echo "   http://YOUR_SERVER_IP:$SERVICE_PORT/webhook/feishu"
echo ""
echo "🔧 管理命令:"
echo "   状态: sudo systemctl status feishu-tts-integration"
echo "   日志: sudo journalctl -u feishu-tts-integration -f"
echo "   重启: sudo systemctl restart feishu-tts-integration"
echo ""
echo "⚠️  下一步:"
echo "   1. 编辑配置文件: vim $SERVICE_DIR/feishu.env"
echo "   2. 重启服务: sudo systemctl restart feishu-tts-integration"
echo "   3. 在飞书开放平台配置事件订阅地址"
echo ""
