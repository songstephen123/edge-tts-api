# API 文档

Edge TTS Service RESTful API 完整文档。

## 目录

- [基础信息](#基础信息)
- [认证](#认证)
- [端点](#端点)
- [错误处理](#错误处理)
- [示例](#示例)

---

## 基础信息

- **Base URL**: `http://your-domain.com` 或 `http://localhost:8000`
- **Content-Type**: `application/json`
- **响应格式**: JSON 或二进制音频数据

---

## 认证

当前版本无需认证。生产环境建议添加 API Key 或 OAuth 认证。

---

## 端点

### 1. 文本转语音

将文本转换为语音音频。

**请求**

```http
POST /tts
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| text | string | 是 | - | 要转换的文本 (1-5000 字符) |
| voice | string | 否 | zh-CN-XiaoxiaoNeural | 音色 ID 或简称 |
| rate | string | 否 | +0% | 语速 (-50% ~ +100%) |
| pitch | string | 否 | +0Hz | 音调 (-50Hz ~ +50Hz) |
| volume | string | 否 | +0% | 音量 (-50% ~ +100%) |

**请求示例**

```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，世界",
    "voice": "xiaoxiao",
    "rate": "+10%"
  }' \
  --output speech.mp3
```

**响应**

- **Content-Type**: `audio/mpeg`
- **Body**: 二进制音频数据 (MP3 格式)
- **Headers**:
  - `X-Voice-Used`: 实际使用的音色 ID
  - `Content-Length`: 音频数据大小（字节）

---

### 2. 获取音色列表

获取所有可用音色。

**请求**

```http
GET /voices
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| locale | string | 否 | 筛选语言 (如: zh-CN, en-US) |
| gender | string | 否 | 筛选性别 (Male, Female) |

**请求示例**

```bash
# 获取所有音色
curl http://localhost:8000/voices

# 获取中文音色
curl http://localhost:8000/voices?locale=zh-CN

# 获取女声音色
curl http://localhost:8000/voices?gender=Female
```

**响应**

```json
{
  "voices": [
    {
      "name": "Microsoft Server Speech Text to Speech Voice (zh-CN, XiaoxiaoNeural)",
      "id": "zh-CN-XiaoxiaoNeural",
      "locale": "zh-CN",
      "locale_name": "Chinese (Mainland)",
      "gender": "Female",
      "description": "Xiaoxiao Neural Chinese voice"
    }
  ],
  "total": 1
}
```

---

### 3. 获取中文音色

快捷获取所有中文音色。

**请求**

```http
GET /voices/chinese
```

**响应**：同 `/voices` 端点

---

### 4. 获取英文音色

快捷获取所有英文音色。

**请求**

```http
GET /voices/english
```

**响应**：同 `/voices` 端点

---

### 5. 获取常用音色

获取精选的常用音色。

**请求**

```http
GET /voices/popular
```

**响应**

```json
{
  "chinese": [
    {"id": "zh-CN-XiaoxiaoNeural", "name": "晓晓 (女声)", "gender": "Female"},
    {"id": "zh-CN-XiaoyiNeural", "name": "晓伊 (女声)", "gender": "Female"},
    {"id": "zh-CN-YunyangNeural", "name": "云扬 (男声)", "gender": "Male"}
  ],
  "english": [
    {"id": "en-US-AriaNeural", "name": "Aria (女声)", "gender": "Female"},
    {"id": "en-US-GuyNeural", "name": "Guy (男声)", "gender": "Male"}
  ]
}
```

---

### 6. 健康检查

检查服务运行状态。

**请求**

```http
GET /health
```

**响应**

```json
{
  "status": "healthy",
  "service": "edge-tts-service",
  "version": "1.0.0",
  "edge_tts_available": true
}
```

---

### 7. 服务信息

获取服务基本信息。

**请求**

```http
GET /
```

**响应**

```json
{
  "service": "Edge TTS Service",
  "version": "1.0.0",
  "description": "基于微软 Edge TTS 的文本转语音 API 服务",
  "docs": "/docs",
  "health": "/health",
  "endpoints": {
    "tts": "POST /tts",
    "voices": "GET /voices",
    "health": "GET /health"
  }
}
```

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

### 错误响应格式

```json
{
  "success": false,
  "error": "错误描述",
  "detail": "详细错误信息（仅 DEBUG 模式）"
}
```

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `text` is required | 未提供文本 | 确保请求包含 `text` 字段 |
| Invalid voice | 音色 ID 不存在 | 使用 `/voices` 获取有效音色 |
| Rate limit exceeded | 请求过于频繁 | 稍后重试 |
| Service unavailable | Edge TTS 服务不可用 | 检查网络连接 |

---

## 示例

### Python

```python
import requests

# 文本转语音
response = requests.post(
    "http://localhost:8000/tts",
    json={"text": "你好，世界", "voice": "xiaoxiao"}
)

with open("speech.mp3", "wb") as f:
    f.write(response.content)

# 获取音色列表
response = requests.get("http://localhost:8000/voices/chinese")
voices = response.json()
print(voices)
```

### JavaScript/Node.js

```javascript
// 文本转语音
const response = await fetch('http://localhost:8000/tts', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    text: '你好，世界',
    voice: 'xiaoxiao'
  })
});

const audio = await response.blob();
// 处理音频...

// 获取音色列表
const voicesRes = await fetch('http://localhost:8000/voices/chinese');
const voices = await voicesRes.json();
console.log(voices);
```

### cURL

```bash
# 文本转语音
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"你好，世界"}' \
  --output speech.mp3

# 获取音色列表
curl http://localhost:8000/voices/chinese
```

---

## 交互式文档

访问 `/docs` 查看 Swagger UI 交互式文档：

```
http://localhost:8000/docs
```

访问 `/redoc` 查看 ReDoc 文档：

```
http://localhost:8000/redoc
```
