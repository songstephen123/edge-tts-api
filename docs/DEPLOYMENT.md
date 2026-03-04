# 部署指南

本文档介绍如何在不同环境中部署 Edge TTS Service。

## 目录

- [本地开发](#本地开发)
- [Docker 部署](#docker-部署)
- [云服务器部署](#云服务器部署)
- [反向代理配置](#反向代理配置)
- [生产环境优化](#生产环境优化)

---

## 本地开发

### 1. 克隆项目

```bash
git clone https://github.com/your-username/edge-tts-skill.git
cd edge-tts-skill
```

### 2. 安装依赖

```bash
# 使用安装脚本（推荐）
bash scripts/install.sh

# 或手动安装
pip install -r requirements.txt
```

### 3. 启动服务

```bash
# 使用启动脚本
bash scripts/start.sh

# 或直接运行
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 验证服务

```bash
# 新终端窗口
bash scripts/health.sh

# 或访问
curl http://localhost:8000/health
```

---

## Docker 部署

### 1. 使用 Docker Compose（推荐）

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 2. 使用 Docker 命令

```bash
# 构建镜像
docker build -t edge-tts-service .

# 运行容器
docker run -d \
  --name edge-tts-service \
  -p 8000:8000 \
  edge-tts-service

# 查看日志
docker logs -f edge-tts-service

# 停止容器
docker stop edge-tts-service
```

### 3. 环境变量配置

通过 `docker-compose.yml` 或 `.env` 文件配置：

```bash
# .env
SERVICE_PORT=8000
LOG_LEVEL=INFO
DEFAULT_VOICE=zh-CN-XiaoxiaoNeural
```

---

## 云服务器部署

### 系统要求

- Linux 系统（Ubuntu 20.04+ 推荐）
- Python 3.10+
- 至少 512MB 内存
- 开放 8000 端口（或自定义端口）

### Ubuntu/Debian 部署

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装 Python 和 pip
sudo apt install -y python3 python3-pip python3-venv

# 3. 克隆项目
git clone https://github.com/your-username/edge-tts-skill.git
cd edge-tts-skill

# 4. 创建虚拟环境并安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 6. 安装并配置 supervisor（保持服务运行）
sudo apt install -y supervisor

# 创建 supervisor 配置
sudo tee /etc/supervisor/conf.d/edge-tts-service.conf > /dev/null <<EOF
[program:edge-tts-service]
directory=/root/edge-tts-skill
command=/root/edge-tts-skill/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
autostart=true
autorestart=true
stderr_logfile=/var/log/edge-tts-service.err.log
stdout_logfile=/var/log/edge-tts-service.out.log
user=root
EOF

# 7. 启动服务
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start edge-tts-service

# 8. 检查状态
sudo supervisorctl status edge-tts-service
```

### 使用 Systemd

```bash
# 创建 systemd 服务文件
sudo tee /etc/systemd/system/edge-tts-service.service > /dev/null <<EOF
[Unit]
Description=Edge TTS Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/edge-tts-skill
Environment="PATH=/root/edge-tts-skill/venv/bin"
ExecStart=/root/edge-tts-skill/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动并开机自启
sudo systemctl daemon-reload
sudo systemctl enable edge-tts-service
sudo systemctl start edge-tts-service

# 查看状态
sudo systemctl status edge-tts-service
```

---

## 反向代理配置

### Nginx

```nginx
# /etc/nginx/sites-available/edge-tts-service
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 对于长音频，增加超时时间
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}

# 启用配置
sudo ln -s /etc/nginx/sites-available/edge-tts-service /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Caddy（自动 HTTPS）

```caddyfile
# Caddyfile
your-domain.com {
    reverse_proxy 127.0.0.1:8000
}
```

---

## 生产环境优化

### 1. 使用 Gunicorn（推荐）

```bash
# 安装 gunicorn
pip install gunicorn

# 启动服务
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile -
```

### 2. 启用缓存

在 `.env` 中配置：

```bash
ENABLE_CACHE=true
CACHE_TTL=3600
```

### 3. 监控和日志

```bash
# 安装监控工具
pip install prometheus-client

# 访问指标端点
curl http://localhost:8000/metrics
```

### 4. 防火墙配置

```bash
# Ubuntu UFW
sudo ufw allow 8000/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS firewalld
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

---

## 故障排查

### 服务无法启动

```bash
# 检查端口占用
sudo lsof -i :8000

# 检查日志
sudo journalctl -u edge-tts-service -n 50

# 测试 Python 环境
python3 -c "import edge_tts; print('OK')"
```

### Docker 问题

```bash
# 查看容器日志
docker logs edge-tts-service

# 重新构建镜像
docker-compose build --no-cache

# 清理并重启
docker-compose down -v
docker-compose up -d
```

### 网络问题

```bash
# 测试 Edge TTS 连通性
curl -v https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1

# 检查 DNS
nslookup speech.platform.bing.com
```

---

## 安全建议

1. **使用反向代理** - 不要直接暴露 8000 端口
2. **配置 HTTPS** - 使用 Let's Encrypt 获取免费证书
3. **限制访问** - 使用防火墙限制可访问的 IP
4. **添加认证** - 对于生产环境，考虑添加 API Key 认证
5. **定期更新** - 保持依赖包最新版本
