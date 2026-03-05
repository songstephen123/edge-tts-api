# 飞书集成指南

本文档说明如何将 Edge TTS API 集成到您已有的飞书应用中。

---

## 📋 前置条件

1. ✅ 已有飞书企业自建应用
2. ✅ Edge TTS API 已部署（http://115.190.252.250:8000）
3. ✅ 有飞书应用的 App ID 和 App Secret

---

## 🚀 快速部署

### 第一步：部署集成服务

```bash
# 将集成服务上传到服务器
scp ~/edge-tts-skill/scripts/deploy-feishu-integration.sh root@115.190.252.250:/root/
scp ~/edge-tts-skill/feishu_integration_service.py root@115.190.252.250:/root/

# SSH 连接到服务器
ssh root@115.190.252.250

# 运行部署脚本
bash /root/deploy-feishu-integration.sh
```

### 第二步：配置飞书应用信息

```bash
# 编辑配置文件
vim /opt/feishu-tts-integration/feishu.env
```

填入您的飞书应用信息：

```bash
# 从飞书开放平台获取
FEISHU_APP_ID=cli_xxxxxxxxxxxxx
FEISHI_APP_SECRET=xxxxxxxxxxxxxxxxxxxx
FEISHI_VERIFICATION_TOKEN=xxxxxxxx
FEISHI_ENCRYPT_KEY=xxxxxxxxxxxxxxxx

# TTS 服务地址
TTS_API_URL=http://115.190.252.250:8000/tts

# 集成服务端口
SERVICE_PORT=8001
```

### 第三步：重启服务

```bash
systemctl restart feishu-tts-integration
systemctl status feishu-tts-integration
```

---

## ⚙️ 飞书开放平台配置

### 1. 事件订阅

在您的飞书应用中配置事件订阅：

1. 进入[飞书开放平台](https://open.feishu.cn/)
2. 选择您的应用 →「事件订阅」
3. 配置请求 URL：
   ```
   http://115.190.252.250:8001/webhook/feishu
   ```
4. 选择订阅事件：
   - ✅ `im.message.receive_v1` - 接收消息

### 2. 权限配置

确保应用有以下权限：

| 权限 | 说明 |
|------|------|
| `im:message` | 发送和接收消息 |
| `im:message:group_at_msg` | 群 @ 消息 |
| `im:chat` | 获取会话信息 |

### 3. 发布应用

配置完成后，发布应用使其生效。

---

## 📱 使用方法

### 在飞书中使用

1. 将应用添加到群聊或单聊
2. 发送消息：
   ```
   /tts 你好，世界
   ```
3. 机器人会返回生成的语音

### 支持的命令

| 命令 | 说明 |
|------|------|
| `/tts 文字内容` | 将文字转换为语音 |
| `/语音 文字内容` | 同上 |

### 音色选择

默认使用 `xiaoxiao`（晓晓女声），如需修改音色，编辑 `feishu_integration_service.py`：

```python
# 在 generate_speech 函数调用处修改
audio_data = generate_speech(text, voice="yunyang")  # 改为云扬男声
```

---

## 🔧 服务管理

```bash
# 查看服务状态
sudo systemctl status feishu-tts-integration

# 查看日志
sudo journalctl -u feishu-tts-integration -f

# 重启服务
sudo systemctl restart feishu-tts-integration

# 停止服务
sudo systemctl stop feishu-tts-integration
```

---

## 🔍 故障排查

### 问题 1：服务无法启动

```bash
# 查看详细日志
sudo journalctl -u feishu-tts-integration -n 50
```

### 问题 2：飞书无响应

1. 检查服务状态
2. 检查事件订阅 URL 是否正确
3. 检查应用权限是否已配置
4. 检查应用是否已发布

### 问题 3：语音生成失败

1. 检查 TTS 服务是否正常：
   ```bash
   curl http://localhost:8000/health
   ```
2. 检查集成服务配置中的 TTS_API_URL

---

## 📊 架构说明

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   飞书应用   │────▶│  集成服务        │────▶│  TTS API    │
│             │     │  (8001端口)      │     │  (8000端口)  │
└─────────────┘     └──────────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  返回语音    │
                    └─────────────┘
```

---

## 🎯 下一步

1. **测试基本功能** - 在飞书中发送 `/tts 测试`
2. **自定义音色** - 修改代码中的默认音色
3. **添加更多功能** - 如语音参数调整、多语言支持等
