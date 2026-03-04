# 腾讯云 Ubuntu 部署指南

## 前置条件

- 腾讯云服务器（Ubuntu 20.04+）
- 具有 sudo 权限的用户
- 服务器内存 ≥ 512MB
- 已开放安全组端口 8000

---

## 方法一：一键部署脚本（推荐）

### 1. 上传项目到服务器

```bash
# 在本地压缩项目
cd ~
tar -czf edge-tts-skill.tar.gz edge-tts-skill/

# 上传到服务器（替换为您的服务器 IP）
scp edge-tts-skill.tar.gz root@YOUR_SERVER_IP:/root/

# 或使用 rsync
rsync -avz ~/edge-tts-skill/ root@YOUR_SERVER_IP:/opt/edge-tts-service/
```

### 2. 连接服务器并部署

```bash
# SSH 连接服务器
ssh root@YOUR_SERVER_IP

# 如果上传了压缩包，先解压
cd /opt
mkdir -p edge-tts-service
cd edge-tts-service
tar -xzf ~/edge-tts-skill.tar.gz --strip-components=1

# 运行部署脚本
cd /opt/edge-tts-service
chmod +x scripts/deploy-cloud.sh
sudo bash scripts/deploy-cloud.sh
```

### 3. 验证部署

```bash
# 在服务器上测试
curl http://localhost:8000/health

# 在本地测试（替换为您的服务器 IP）
curl http://YOUR_SERVER_IP:8000/health
```

---

## 方法二：手动部署

### 1. 更新系统

```bash
ssh root@YOUR_SERVER_IP

# 更新系统
apt update && apt upgrade -y

# 安装必要工具
apt install -y python3 python3-pip python3-venv git
```

### 2. 安装项目

```bash
# 创建目录
mkdir -p /opt/edge-tts-service
cd /opt/edge-tts-service

# 上传项目文件（使用 scp 或 rsync）
# 或创建 requirements.txt:
cat > requirements.txt << 'EOF'
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.2
edge-tts==6.1.12
python-multipart==0.0.12
python-dotenv==1.0.1
EOF

# 创建应用代码
# ... (复制 app/ 目录下的所有文件)

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 创建系统服务

```bash
cat > /etc/systemd/system/edge-tts-service.service <<EOF
[Unit]
Description=Edge TTS Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/edge-tts-service
Environment="PATH=/opt/edge-tts-service/venv/bin:/usr/local/bin"
ExecStart=/opt/edge-tts-service/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl enable edge-tts-service
systemctl start edge-tts-service
```

---

## 腾讯云安全组配置

### 1. 登录腾讯云控制台

1. 进入「云服务器控制台」
2. 选择您的实例
3. 点击「安全组」→「配置规则」

### 2. 添加入站规则

| 类型 | 协议 | 端口 | 源 | 说明 |
|------|------|------|-----|------|
| 自定义 | TCP | 8000 | 0.0.0.0/0 | TTS 服务（生产环境建议限制 IP） |

---

## 测试服务

### 健康检查

```bash
curl http://YOUR_SERVER_IP:8000/health
```

**预期响应：**
```json
{
  "status": "healthy",
  "service": "edge-tts-service",
  "version": "1.0.0",
  "edge_tts_available": true
}
```

### TTS 测试

```bash
curl -X POST http://YOUR_SERVER_IP:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"你好，世界"}' \
  --output test.mp3
```

---

## 飞书集成

### 1. 配置飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建应用 → 获取 App ID 和 App Secret
3. 配置权限：`im:message`
4. 配置事件订阅：`http://YOUR_SERVER_IP:8000/feishu/webhook`

### 2. 简化方案：使用飞书自定义机器人

```python
# 在您的应用中调用 TTS 服务
import requests

TTS_API = "http://YOUR_SERVER_IP:8000/tts"

def send_voice_message(text):
    # 生成语音
    response = requests.post(TTS_API, json={"text": text})
    audio_file = response.content

    # 发送到飞书（使用飞书 SDK）
    # ...
```

---

## 常用命令

```bash
# 查看服务状态
sudo systemctl status edge-tts-service

# 查看实时日志
sudo journalctl -u edge-tts-service -f

# 重启服务
sudo systemctl restart edge-tts-service

# 停止服务
sudo systemctl stop edge-tts-service

# 查看端口占用
netstat -tulnp | grep 8000
```

---

## 故障排查

### 1. 服务无法启动

```bash
# 查看详细日志
sudo journalctl -u edge-tts-service -n 50

# 检查端口
netstat -tulnp | grep 8000

# 手动测试
cd /opt/edge-tts-service
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. 无法访问服务

- 检查安全组是否开放 8000 端口
- 检查防火墙：`sudo ufw status`
- 检查服务状态：`sudo systemctl status edge-tts-service`

### 3. Edge TTS 连接失败

```bash
# 测试网络连通性
curl -v https://speech.platform.bing.com

# 检查 DNS
nslookup speech.platform.bing.com
```

---

## 安全建议

1. **限制访问 IP** - 在安全组中只允许可信 IP 访问
2. **使用 HTTPS** - 配置 Nginx + Let's Encrypt
3. **添加认证** - 实现简单的 API Key 认证
4. **定期更新** - 保持系统和依赖包最新
