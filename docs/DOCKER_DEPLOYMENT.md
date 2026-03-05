# Docker 部署指南

## 🐳 完整的 Docker 部署方案

### 特性

- ✅ 基于 Python 3.11-slim
- ✅ 包含 FFmpeg 和 opus-tools（Opus 转换）
- ✅ 优化镜像大小（多阶段构建）
- ✅ 支持缓存和持久化存储
- ✅ 自动健康检查
- ✅ 一键部署和更新

---

## 📋 部署步骤

### 方案 A：本地 Docker 部署

```bash
# 1. 进入项目目录
cd ~/edge-tts-skill

# 2. 构建并启动
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 访问服务
open http://localhost:8000/docs
```

---

### 方案 B：服务器 Docker 部署

#### 第一步：安装 Docker

```bash
# SSH 登录服务器
ssh root@115.190.252.250

# 下载并运行 Docker 安装脚本
mkdir -p ~/scripts
curl -fsSL https://raw.githubusercontent.com/songstephen123/edge-tts-api/main/scripts/install-docker-server.sh -o ~/scripts/install-docker.sh
chmod +x ~/scripts/install-docker.sh
bash ~/scripts/install-docker.sh
```

#### 第二步：准备文件

```bash
# 在本地压缩项目
cd ~/edge-tts-skill
tar -czf edge-tts-docker.tar.gz . --exclude='.git' --exclude='__pycache__' --exclude='*.pyc'
```

#### 第三步：上传到服务器

```bash
scp edge-tts-docker.tar.gz root@115.190.252.250:/root/
```

#### 第四步：SSH 并部署

```bash
ssh root@115.190.252.250

# 解压
mkdir -p /opt/edge-tts-service-docker
cd /opt/edge-tts-service-docker
tar -xzf ~/edge-tts-docker.tar.gz --strip-components=1

# 运行部署脚本
bash scripts/docker-deploy-server.sh
```

---

## 🔧 Docker 管理命令

### 基础命令

```bash
cd /opt/edge-tts-service-docker

# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

### 高级命令

```bash
# 进入容器
docker-compose exec edge-tts-service bash

# 查看资源使用
docker stats

# 清理未使用的镜像
docker image prune

# 清理未使用的卷
docker volume prune
```

---

## 📁 持久化存储

### 缓存目录

```yaml
volumes:
  tts_cache:
    driver: local
```

- **用途**: 存储预转换的音频文件
- **位置**: Docker volume
- **清理**: 定期清理过期文件

### 音频输出目录

```yaml
volumes:
  tts_audio:
    driver: local
```

- **用途**: 存储生成的音频文件
- **访问**: `http://server:8000/static/audio/`
- **清理**: 可手动清理或设置定时任务

---

## 🔄 更新部署

### 更新代码

```bash
# 1. 重新打包
cd ~/edge-tts-skill
tar -czf edge-tts-docker.tar.gz . --exclude='.git'

# 2. 上传
scp edge-tts-docker.tar.gz root@115.190.252.250:/root/

# 3. SSH 并更新
ssh root@115.190.252.250
cd /opt/edge-tts-service-docker
tar -xzf ~/edge-tts-docker.tar.gz --strip-components=1

# 4. 重新构建
docker-compose down
docker-compose build
docker-compose up -d
```

---

## 🧪 验证部署

### 健康检查

```bash
curl http://localhost:8000/health
```

### 测试 Opus 转换

```bash
curl -X POST http://localhost:8000/tts/feishu \
  -H "Content-Type: application/json" \
  -d '{"text":"测试"}' \
  | python3 -m json.tool
```

### 检查 FFmpeg 和 opusenc

```bash
# 进入容器
docker-compose exec edge-tts-service bash

# 检查 FFmpeg
ffmpeg -version | grep opus

# 检查 opusenc
opusenc --version

# 退出
exit
```

---

## ⚠️ 故障排查

### 问题 1: 构建失败

```bash
# 查看详细错误
docker-compose build --no-cache

# 清理缓存
docker system prune -a
```

### 问题 2: 启动失败

```bash
# 查看日志
docker-compose logs

# 检查端口占用
netstat -tulnp | grep 8000
```

### 问题 3: 转换失败

```bash
# 进入容器检查
docker-compose exec edge-tts-service bash

# 测试 FFmpeg
ffmpeg -f lavfi -i test.mp3 -t opus test.opus

# 测试 opusenc
opusenc --help
```

---

## 📊 性能优化

### 资源限制

```yaml
services:
  edge-tts-service:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          memory: 512M
```

### 并发配置

```yaml
services:
  edge-tts-service:
    command: >
      uvicorn app.main:app
      --host 0.0.0.0
      --port 8000
      --workers 4
      --worker-class uvicorn.workers.UvicornWorker
```

---

## 🌐 生产环境建议

### 使用 Nginx 反向代理

```yaml
# docker-compose.yml 添加 Nginx
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - edge-tts-service
```

### 配置 HTTPS

```bash
# 使用 Certbot
apt install certbot
certbot --nginx certonly -d your-domain.com
```

---

## 📝 环境变量

通过 `.env` 文件或 docker-compose.yml 配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SERVICE_PORT` | 8000 | 服务端口 |
| `LOG_LEVEL` | INFO | 日志级别 |
| `CORS_ORIGINS` | * | CORS 允许的源 |
| `DEFAULT_VOICE` | zh-CN-XiaoxiaoNeural | 默认音色 |
| `DEFAULT_RATE` | +0% | 默认语速 |

---

**准备好开始部署了吗？** 需要我帮您执行部署吗？
