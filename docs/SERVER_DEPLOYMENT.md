# 服务器部署指南

## 快速部署

### 1. 打包项目

```bash
cd /Users/songstephen/edge-tts-skill
tar -czf edge-tts-multi-provider.tar.gz . --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv' --exclude='test*.mp3' --exclude='test*.wav'
```

### 2. 上传到服务器

```bash
scp edge-tts-multi-provider.tar.gz root@115.190.252.250:/root/
```

### 3. SSH 部署

```bash
ssh root@115.190.252.250

# 停止现有服务
cd /opt/edge-tts-service-docker
docker-compose down

# 备份
cp -r . ../edge-tts-backup-$(date +%Y%m%d)

# 解压新版本
cd /opt
rm -rf edge-tts-service-docker
mkdir -p edge-tts-service-docker
cd edge-tts-service-docker
tar -xzf ~/edge-tts-multi-provider.tar.gz --strip-components=1

# 启动服务
docker-compose down
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

### 4. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 提供者列表
curl http://localhost:8000/tts/providers

# 生成测试语音
curl -X POST http://localhost:8000/tts/feishu \
  -H "Content-Type: application/json" \
  -d '{"text": "测试"}'
```

## 环境变量

在服务器上创建 `.env` 文件：

```bash
TTS_FAILURE_THRESHOLD=5
TTS_COOLDOWN_SECONDS=300
TTS_ENABLE_CACHE=true
```

## 故障排查

### 查看 Docker 日志

```bash
docker-compose logs -f edge-tts-service
```

### 重启服务

```bash
docker-compose restart
```

### 检查端口占用

```bash
netstat -tulnp | grep 8000
```
