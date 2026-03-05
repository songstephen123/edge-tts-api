#!/bin/bash
# 配置 Docker 国内镜像源

echo "🔧 配置 Docker 镜像加速器..."
echo "======================================================"

# 创建 Docker 配置目录
mkdir -p /etc/docker

# 配置国内镜像源
cat > /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://docker.1panel.live",
    "https://docker.chenby.cn",
    "https://docker.awsl9527.cn",
    "https://dockerpull.org"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF

echo "✅ 配置文件已创建: /etc/docker/daemon.json"
echo ""

# 重启 Docker 服务
echo "🔄 重启 Docker 服务..."
systemctl daemon-reload
systemctl restart docker

# 等待 Docker 启动
sleep 3

# 验证配置
echo "📋 当前 Docker 镜像配置:"
docker info | grep -A 5 "Registry Mirrors" || echo "  (使用默认配置)"

echo ""
echo "======================================================"
echo "✅ Docker 镜像源配置完成！"
echo "======================================================"
