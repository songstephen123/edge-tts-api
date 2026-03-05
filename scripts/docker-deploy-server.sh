#!/bin/bash
# 服务器上 Docker 部署脚本

set -e

echo "🐳 Docker 部署 Edge TTS Service（Opus 优化版）"
echo "======================================================"
echo ""

# 工作目录
WORK_DIR="/opt/edge-tts-service-docker"
mkdir -p $WORK_DIR
cd $WORK_DIR

echo "📁 工作目录: $WORK_DIR"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，开始安装..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    echo "✅ Docker 安装完成"
fi

echo ""
echo "📋 准备文件..."
echo "请将以下文件上传到服务器:"
echo "  1. Dockerfile"
echo "  2. docker-compose.yml"
echo "  3. app/ (整个目录)"
echo ""
read -p "文件上传完成后按 Enter 继续..."

# 检查文件
if [ ! -f "Dockerfile" ]; then
    echo "❌ 找不到 Dockerfile"
    exit 1
fi

if [ ! -d "app" ]; then
    echo "❌ 找不到 app 目录"
    exit 1
fi

echo "✅ 文件检查完成"
echo ""

# 停止旧容器
echo "🛑 停止旧容器..."
docker-compose down 2>/dev/null || echo "  无旧容器"

# 构建镜像
echo "🔨 构建 Docker 镜像..."
docker-compose build

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查状态
echo ""
echo "📊 服务状态:"
docker-compose ps

# 测试服务
echo ""
echo "🧪 测试服务..."
sleep 2
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "======================================================"
echo "   部署完成！"
echo "======================================================"
echo ""
echo "🌐 服务地址:"
echo "   http://115.190.252.250:8000/docs"
echo "   http://115.190.252.250:8000/health"
echo ""
echo "📋 管理命令:"
echo "   cd $WORK_DIR"
echo "   docker-compose logs -f      # 查看日志"
echo "   docker-compose restart   # 重启"
echo "   docker-compose down       # 停止"
echo ""
