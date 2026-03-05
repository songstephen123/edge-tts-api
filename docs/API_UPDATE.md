# API 更新说明 - Opus 格式支持

## 🆕 新增功能

### 1. Opus 格式支持

飞书推荐使用 Opus 格式音频。现在 TTS 服务支持自动将 MP3 转换为 Opus。

**转换方式**：使用 FFmpeg 进行实时转换

---

## 📡 新增 API 端点

### POST /tts/feishu - 飞书专用接口

专门为飞书设计的接口，返回 Opus 格式音频 URL。

**请求：**
```json
{
  "text": "你好，世界",
  "voice": "xiaoxiao",
  "rate": "+0%"
}
```

**响应：**
```json
{
  "success": true,
  "audio_url": "http://115.190.252.250:8000/static/audio/xxx.opus",
  "audio_key": "xxx.opus",
  "duration": 2500,
  "text": "你好，世界",
  "text_length": 5,
  "voice_used": "zh-CN-XiaoxiaoNeural"
}
```

**字段说明：**
- `audio_url`: 音频文件 URL（飞书可直接访问）
- `audio_key`: 音频文件名
- `duration`: 音频时长（毫秒）

---

### POST /tts/url - 返回音频 URL

返回音频文件 URL，适用于需要 URL 而非文件数据的场景。

**请求：**
```json
{
  "text": "你好，世界",
  "format": "opus"
}
```

**响应：**
```json
{
  "success": true,
  "url": "http://115.190.252.250:8000/static/audio/xxx.opus",
  "filename": "xxx.opus",
  "format": "opus",
  "text": "你好，世界"
}
```

---

### POST /tts - 支持 format 参数

原有端点新增 `format` 参数。

**请求：**
```json
{
  "text": "你好，世界",
  "format": "opus"
}
```

**参数说明：**
- `format`: 输出格式
  - `mp3`: 默认，MP3 格式
  - `opus`: Opus 格式（推荐用于飞书）

---

## 📁 静态文件访问

生成的音频文件保存在 `/tmp/tts_audio/` 目录，可通过以下 URL 访问：

```
http://115.190.252.250:8000/static/audio/{filename}
```

---

## 🔧 更新部署

### 第一步：更新代码

```bash
# 1. 上传更新的文件
scp app/routes/tts.py root@115.190.252.250:/opt/edge-tts-service/app/routes/
scp app/models/schemas.py root@115.190.252.250:/opt/edge-tts-service/app/models/
scp app/main.py root@115.190.252.250:/opt/edge-tts-service/app/
scp requirements.txt root@115.190.252.250:/opt/edge-tts-service/

# 2. SSH 连接服务器
ssh root@115.190.252.250
```

### 第二步：安装 FFmpeg

```bash
# 安装 ffmpeg（Opus 转换需要）
apt update
apt install -y ffmpeg

# 验证安装
ffmpeg -version
```

### 第三步：更新依赖

```bash
cd /opt/edge-tts-service
source venv/bin/activate
pip install aiofiles
```

### 第四步：重启服务

```bash
systemctl restart edge-tts-service
systemctl status edge-tts-service
```

---

## 🧪 测试新接口

### 测试 Opus 格式

```bash
# 测试飞书专用接口
curl -X POST http://115.190.252.250:8000/tts/feishu \
  -H "Content-Type: application/json" \
  -d '{"text":"测试Opus音频"}' \
  | python3 -m json.tool
```

### 测试 URL 返回

```bash
# 测试 URL 接口
curl -X POST http://115.190.252.250:8000/tts/url \
  -H "Content-Type: application/json" \
  -d '{"text":"测试URL返回","format":"opus"}' \
  | python3 -m json.tool
```

### 直接访问音频文件

```bash
# 生成音频
curl -X POST http://115.190.252.250:8000/tts/feishu \
  -H "Content-Type: application/json" \
  -d '{"text":"测试"}' \
  | python3 -m json.tool

# 从响应中获取 audio_url，然后访问
# 例如：http://115.190.252.250:8000/static/audio/xxx.opus
```

---

## 📱 飞书集成更新

更新后的飞书集成使用新接口：

```python
import requests

# 调用飞书专用接口
response = requests.post(
    "http://115.190.252.250:8000/tts/feishu",
    json={"text": "你好，世界"}
)

result = response.json()

# 获取音频 URL
audio_url = result["audio_url"]
duration = result["duration"]

# 在飞书中使用
# 飞书可以通过 audio_url 直接播放 Opus 音频
```

---

## ⚠️ 注意事项

1. **FFmpeg 依赖**：Opus 转换需要服务器安装 FFmpeg
2. **转换时间**：Opus 转换会增加约 100-200ms 延迟
3. **文件存储**：音频文件存储在 `/tmp/tts_audio/`，定期清理
4. **防火墙**：确保 8000 端口开放

---

## 🗑️ 清理旧音频文件

```bash
# 清理超过 1 天的音频文件
find /tmp/tts_audio/ -name "*.opus" -mtime +1 -delete
find /tmp/tts_audio/ -name "*.mp3" -mtime +1 -delete

# 或添加到 crontab 自动清理
# 0 2 * * * find /tmp/tts_audio/ -name "*.opus" -mtime +1 -delete
```
