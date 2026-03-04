#!/bin/bash
# Edge TTS Service - 云服务器一键部署脚本
# 适用于：Ubuntu/Debian + 腾讯云/阿里云

set -e

echo "🚀 Edge TTS Service 云服务器部署脚本"
echo "====================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}请使用 sudo 运行此脚本${NC}"
    echo "sudo bash $0"
    exit 1
fi

# 获取服务器 IP
SERVER_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "无法获取")
echo -e "${GREEN}服务器 IP: $SERVER_IP${NC}"
echo ""

# 更新系统
echo "📦 更新系统包..."
apt update && apt upgrade -y

# 安装必要工具
echo "🔧 安装必要工具..."
apt install -y python3 python3-pip python3-venv git curl wget ufw

# 创建应用目录
APP_DIR="/opt/edge-tts-service"
echo "📁 创建应用目录: $APP_DIR"
mkdir -p $APP_DIR

# 检查是否已经克隆了项目
if [ -d "$APP_DIR/.git" ]; then
    echo "📥 项目已存在，拉取最新代码..."
    cd $APP_DIR
    git pull
else
    echo "📥 克隆项目..."
    # 注意：需要将此脚本部署到您的 Git 仓库后使用
    # 如果还没有 Git 仓库，可以先复制本地文件
    read -p "🔗 请输入您的 Git 仓库地址 (或按 Enter 跳过，使用本地文件): " GIT_REPO

    if [ -n "$GIT_REPO" ]; then
        git clone $GIT_REPO $APP_DIR
    else
        echo -e "${YELLOW}请手动将项目文件复制到 $APP_DIR${NC}"
        exit 1
    fi
fi

cd $APP_DIR

# 创建虚拟环境
echo "🐍 创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "📦 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 配置防火墙
echo "🔒 配置防火墙..."
ufw allow 22/tcp    # SSH
ufw allow 8000/tcp  # TTS Service
ufw --force enable

# 配置环境变量
echo "⚙️  配置环境变量..."
if [ ! -f .env ]; then
    cp .env.example .env
    # 设置服务器 IP 为允许的 CORS 源
    echo "SERVER_IP=$SERVER_IP" >> .env
fi

# 创建 systemd 服务
echo "🔧 创建系统服务..."
cat > /etc/systemd/system/edge-tts-service.service <<EOF
[Unit]
Description=Edge TTS Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$APP_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重载 systemd 并启动服务
echo "🚀 启动服务..."
systemctl daemon-reload
systemctl enable edge-tts-service
systemctl start edge-tts-service

# 等待服务启动
sleep 3

# 检查服务状态
if systemctl is-active --quiet edge-tts-service; then
    echo -e "${GREEN}✅ 服务启动成功！${NC}"
else
    echo -e "${RED}❌ 服务启动失败，查看日志：${NC}"
    journalctl -u edge-tts-service -n 20 --no-pager
    exit 1
fi

# 显示服务信息
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📊 服务状态:"
echo "   检查状态: sudo systemctl status edge-tts-service"
echo "   查看日志: sudo journalctl -u edge-tts-service -f"
echo "   重启服务: sudo systemctl restart edge-tts-service"
echo "   停止服务: sudo systemctl stop edge-tts-service"
echo ""
echo "🌐 访问地址:"
echo "   API 文档: http://$SERVER_IP:8000/docs"
echo "   健康检查: http://$SERVER_IP:8000/health"
echo "   服务地址: http://$SERVER_IP:8000/tts"
echo ""
echo "🧪 快速测试:"
echo "   curl http://$SERVER_IP:8000/health"
echo "   curl -X POST http://$SERVER_IP:8000/tts \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"text\":\"你好，世界\"}' \\"
echo "     --output test.mp3"
echo ""
echo -e "${YELLOW}⚠️  注意事项:${NC}"
echo "   1. 确保腾讯云安全组已开放 8000 端口"
echo "   2. 建议配置 HTTPS（使用 Let's Encrypt + Nginx）"
echo "   3. 建议配置防火墙只允许特定 IP 访问"
echo ""
