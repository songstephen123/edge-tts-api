#!/bin/bash
# Docker 安装脚本 - 火山引擎服务器专用
# 修复了命令格式和网络重试问题

set -e

echo "🐳 开始安装 Docker..."
echo "======================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检测系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
    echo -e "${YELLOW}检测到系统: $PRETTY_NAME${NC}"
else
    echo -e "${RED}无法检测系统版本${NC}"
    exit 1
fi

# 更新包索引
echo -e "${YELLOW}更新包索引...${NC}"
apt-get update -qq

# 安装必要依赖
echo -e "${YELLOW}安装依赖包...${NC}"
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 创建 keyrings 目录
echo -e "${YELLOW}配置 Docker GPG 密钥...${NC}"
install -m 0755 -d /etc/apt/keyrings

# 下载 GPG 密钥（使用国内镜像 + 重试机制）
echo -e "${YELLOW}下载 Docker GPG 密钥...${NC}"

# 尝试多个镜像源
GPG_URLS=(
    "https://download.docker.com/linux/ubuntu/gpg"
    "https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg"
    "https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/ubuntu/gpg"
)

GPG_DOWNLOADED=false
for GPG_URL in "${GPG_URLS[@]}"; do
    echo "  尝试: $GPG_URL"
    if curl -fsSL "$GPG_URL" -o /tmp/docker.gpg 2>/dev/null; then
        # 验证下载的文件
        if [ -s /tmp/docker.gpg ]; then
            cat /tmp/docker.gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            chmod a+r /etc/apt/keyrings/docker.gpg
            echo -e "${GREEN}✅ GPG 密钥下载成功${NC}"
            GPG_DOWNLOADED=true
            break
        fi
    fi
    echo "  失败，尝试下一个..."
done

if [ "$GPG_DOWNLOADED" = false ]; then
    echo -e "${RED}❌ 所有镜像源均失败，尝试使用非 HTTPS 方式...${NC}"
    # 备用方案：直接添加 Docker 官方仓库（不验证 GPG）
    echo -e "${YELLOW}使用不安全模式继续...${NC}"
fi

# 添加 Docker 仓库
echo -e "${YELLOW}添加 Docker APT 仓库...${NC}"

if [ "$GPG_DOWNLOADED" = true ]; then
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $VERSION_CODENAME stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
else
    # 使用阿里云镜像（无需 GPG）
    echo \
      "deb [arch=$(dpkg --print-architecture)] https://mirrors.aliyun.com/docker-ce/linux/ubuntu \
      $VERSION_CODENAME stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
fi

# 更新包索引
echo -e "${YELLOW}更新 APT 索引...${NC}"
apt-get update -qq

# 安装 Docker
echo -e "${YELLOW}安装 Docker Engine...${NC}"
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 启动 Docker
echo -e "${YELLOW}启动 Docker 服务...${NC}"
systemctl start docker
systemctl enable docker

# 验证安装
echo ""
echo -e "${YELLOW}验证 Docker 安装...${NC}"
docker --version
docker compose version

# 运行测试容器
echo -e "${YELLOW}运行测试容器...${NC}"
docker run --rm hello-world

echo ""
echo "======================================================"
echo -e "${GREEN}✅ Docker 安装完成！${NC}"
echo "======================================================"
echo ""
echo "📋 下一步："
echo "   1. 上传项目文件到服务器"
echo "   2. 运行: cd /opt/edge-tts-service-docker"
echo "   3. 运行: docker-compose up -d"
echo ""
