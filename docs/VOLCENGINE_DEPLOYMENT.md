# 火山引擎 Ubuntu 部署指南

## 前置条件

- 火山引擎云服务器（Ubuntu 20.04+）
- 具有 sudo 权限的用户
- 服务器内存 ≥ 512MB
- 已开放安全组端口 8000

---

## 方法一：一键部署脚本（推荐）

### 1. 上传项目到服务器

```bash
# 在本地电脑执行
cd ~
tar -czf edge-tts-skill.tar.gz edge-tts-skill/

# 上传到服务器（替换 YOUR_SERVER_IP）
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
apt install -y python3 python3-pip python3-venv git curl
```

### 2. 安装项目

```bash
# 创建目录
mkdir -p /opt/edge-tts-service
cd /opt/edge-tts-service

# 上传项目文件（使用 scp 或 rsync）
# 如果使用 rsync:
# rsync -avz ~/edge-tts-skill/ root@YOUR_SERVER_IP:/opt/edge-tts-service/

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
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
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl enable edge-tts-service
systemctl start edge-tts-service
```

---

## 火山引擎安全组配置

### 1. 登录火山引擎控制台

1. 访问 [火山引擎控制台](https://console.volcengine.com/)
2. 进入「云服务器 ECS」
3. 找到您的实例

### 2. 配置安全组

**方式一：通过实例详情页**

1. 点击实例 ID 进入详情页
2. 点击「安全组」标签
3. 点击「配置规则」或「添加规则」

**方式二：通过安全组页面**

1. 左侧菜单选择「安全组」
2. 找到对应的安全组
3. 点击「配置规则」

### 3. 添加入站规则

点击「添加入站规则」，填写：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 协议端口 | 自定义 TCP | 端口范围输入 8000 |
| 端口范围 | 8000 | TTS 服务端口 |
| 授权对象 | 0.0.0.0/0 | 允许所有 IP（生产环境建议限制） |
| 描述 | TTS Service | 规则说明 |

点击「确定」保存。

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

### 访问 API 文档

浏览器访问：`http://YOUR_SERVER_IP:8000/docs`

---

## 飞书集成

### 方案一：飞书机器人（简化版）

创建一个简单的服务，接收飞书消息并调用 TTS：

```python
# feishu_bot.py
from fastapi import FastAPI, Request
import requests

app = FastAPI()
TTS_API = "http://localhost:8000/tts"  # 如果在同一服务器

@app.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    body = await request.json()

    # 处理消息
    if body.get("event", {}).get("type") == "message":
        text = body["event"]["text"][""]

        # 解析 TTS 命令，如 "/tts 你好"
        if text.startswith("/tts "):
            tts_text = text.split(" ", 1)[1]

            # 调用 TTS 服务
            tts_response = requests.post(
                TTS_API,
                json={"text": tts_text}
            )

            # 保存音频并返回飞书消息链接
            # ...

    return {"code": 0}
```

### 方案二：飞书自定义机器人（推荐）

使用飞书群自定义机器人 Webhook：

```python
import requests

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
TTS_API = "http://YOUR_SERVER_IP:8000/tts"

def send_tts_to_feishu(text):
    # 生成语音
    tts_res = requests.post(TTS_API, json={"text": text})

    # 发送消息到飞书
    # 注意：飞书自定义机器人直接发送音频较复杂
    # 建议先发送文字消息 + 音频文件链接
    requests.post(FEISHU_WEBHOOK, json={
        "msg_type": "text",
        "content": {"text": f"🔊 语音已生成: {text}"}
    })
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
# 或
ss -tulnp | grep 8000
```

---

## 故障排查

### 1. 服务无法启动

```bash
# 查看详细日志
sudo journalctl -u edge-tts-service -n 50

# 检查端口是否被占用
sudo netstat -tulnp | grep 8000

# 手动运行测试
cd /opt/edge-tts-service
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. 无法从外网访问

**检查清单：**

1. ✅ 安全组是否开放 8000 端口
   - 登录火山引擎控制台检查

2. ✅ 服务器防火墙状态
   ```bash
   sudo ufw status
   # 如果需要开放端口
   sudo ufw allow 8000/tcp
   ```

3. ✅ 服务是否正在运行
   ```bash
   sudo systemctl status edge-tts-service
   ```

4. ✅ 服务器内网 IP 是否正确监听
   ```bash
   netstat -tulnp | grep 8000
   # 应该看到 0.0.0.0:8000
   ```

### 3. Edge TTS 连接失败

```bash
# 测试能否访问 Edge TTS 服务
curl -v https://speech.platform.bing.com

# 检查 DNS 解析
nslookup speech.platform.bing.com

# 测试 TTS 功能
cd /opt/edge-tts-service
source venv/bin/activate
python3 -c "import edge_tts; import asyncio; asyncio.run(edge_tts.Communicate('测试').save('test.mp3'))"
```

---

## 安全建议

1. **限制访问 IP**
   - 在安全组中只允许可信 IP 访问 8000 端口
   - 或使用防火墙规则限制来源

2. **使用 HTTPS**
   - 配置 Nginx 反向代理
   - 使用 Let's Encrypt 免费证书

3. **添加 API 认证**
   - 实现简单的 API Key 验证
   - 或使用 JWT Token

4. **定期更新**
   ```bash
   # 更新系统
   sudo apt update && sudo apt upgrade -y

   # 更新 Python 依赖
   cd /opt/edge-tts-service
   source venv/bin/activate
   pip install --upgrade -r requirements.txt
   ```

---

## 性能优化（可选）

### 使用 Gunicorn（生产环境推荐）

```bash
# 安装 gunicorn
pip install gunicorn

# 修改 systemd 服务配置
sudo vim /etc/systemd/system/edge-tts-service.service

# 将 ExecStart 改为：
# ExecStart=/opt/edge-tts-service/venv/bin/gunicorn app.main:app \
#   --workers 4 \
#   --worker-class uvicorn.workers.UvicornWorker \
#   --bind 0.0.0.0:8000 \
#   --timeout 300

# 重启服务
sudo systemctl daemon-reload
sudo systemctl restart edge-tts-service
```

---

## 监控（可选）

### 简单健康监控脚本

```bash
# /opt/edge-tts-service/scripts/monitor.sh
#!/bin/bash
HEALTH_URL="http://localhost:8000/health"
response=$(curl -s "$HEALTH_URL")

if echo "$response" | grep -q '"status":"healthy"'; then
    echo "$(date): Service is healthy"
else
    echo "$(date): Service is down!"
    # 可以添加发送告警的逻辑
fi
```

添加到 crontab 定时检查：
```bash
# 每 5 分钟检查一次
crontab -e
# 添加: */5 * * * * /opt/edge-tts-service/scripts/monitor.sh >> /var/log/tts-monitor.log 2>&1
```
