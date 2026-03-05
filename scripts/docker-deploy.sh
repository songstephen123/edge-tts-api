#!/bin/bash
# Docker 部署脚本 - 一键部署 TTS 服务

set -e

echo "🐳 Docker 部署 Edge TTS Service（Opus 优化版）"
echo "======================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查 Docker
echo -e "${YELLOW}检查 Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    echo "   Ubuntu/Debian: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    echo "   CentOS/RHEL: yum install -y docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    echo "   安装方法: sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-uname -m\" -o /usr/local/bin/docker-compose"
    echo "   或: sudo apt install docker-compose"
    exit 1
fi

echo -e "${GREEN}✅ Docker 环境正常${NC}"
echo ""

# 停止旧容器
echo -e "${YELLOW}停止旧容器...${NC}"
docker-compose down 2>/dev/null || echo "  无旧容器"
echo ""

# 构建镜像
echo -e "${YELLOW}构建 Docker 镜像...${NC}"
docker-compose build
echo ""

# 启动服务
echo -e "${YELLOW}启动服务...${NC}"
docker-compose up -d
echo ""

# 等待启动
echo -e "${YELLOW}等待服务启动...${NC}"
sleep 5
echo ""

# 检查状态
echo -e "${YELLOW}检查服务状态...${NC}"
docker-compose ps
echo ""

# 测试服务
echo -e "${YELLOW}测试服务...${NC}"
sleep 2
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)

if [ -n "$HEALTH_RESPONSE" ]; then
    echo -e "${GREEN}✅ 服务启动成功！${NC}"
    echo ""
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo -e "${YELLOW}⚠️  服务可能还在启动中${NC}"
    echo "   查看日志: docker-compose logs -f"
fi

echo ""
echo "======================================================"
echo -e "${GREEN}   部署完成！${NC}"
echo "======================================================"
echo ""
echo "🌐 访问地址:"
echo "   API 文档: http://localhost:8000/docs"
echo "   健康检查: http://localhost:8000/health"
echo ""
echo "📊 性能测试:"
echo "   curl -X POST http://localhost:8000/tts/feishu \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"text\":\"测试\"}'"
echo ""
echo "📋 管理命令:"
echo "   查看日志: docker-compose logs -f"
echo "   重启服务: docker-compose restart"
echo "   停止服务: docker-compose down"
echo "   查看性能: curl http://localhost:8000/tts/performance"
echo ""
