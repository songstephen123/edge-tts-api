#!/bin/bash
# 服务器部署脚本

SERVER="root@115.190.252.250"
PROJECT_DIR="/opt/edge-tts-service-docker"

echo "📦 打包项目..."
tar -czf edge-tts-multi-provider.tar.gz . \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.venv' \
  --exclude='test*.mp3' \
  --exclude='test*.wav'

echo "📤 上传到服务器..."
scp edge-tts-multi-provider.tar.gz $SERVER:/root/

echo "🚀 部署中..."
ssh $SERVER bash << 'ENDSSH'
cd $PROJECT_DIR
docker-compose down
tar -xzf ~/edge-tts-multi-provider.tar.gz --strip-components=1
docker-compose up -d --build
docker-compose logs -f --tail=50
ENDSSH

echo "✅ 部署完成！"
