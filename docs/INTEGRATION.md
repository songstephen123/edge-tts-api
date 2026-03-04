# 集成指南

本文档介绍如何将 Edge TTS Service 集成到各种应用中。

## 目录

- [飞书机器人](#飞书机器人)
- [钉钉机器人](#钉钉机器人)
- [微信机器人](#微信机器人)
- [Telegram Bot](#telegram-bot)
- [Web 应用](#web-应用)
- [移动应用](#移动应用)

---

## 飞书机器人

### 方案概述

飞书可以通过 Webhook 接收消息，调用 TTS 服务生成语音后返回。

### 实现步骤

#### 1. 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 App ID 和 App Secret

#### 2. 配置权限

在权限管理中添加：
- `im:message` - 接收消息
- `im:message:group_at_msg` - 群聊 @ 消息
- `im:message:send_at_msg` - 发送消息

#### 3. 配置事件订阅

1. 在「事件订阅」中配置请求 URL：
   ```
   https://your-domain.com/feishu/webhook
   ```

2. 填写验证凭证（加密 Key 和 Token）

3. 订阅事件：`im.message.receive_v1`

#### 4. 部署 Webhook 服务

```python
from fastapi import FastAPI, Request
import requests

app = FastAPI()

@app.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    body = await request.json()

    # URL 验证
    if body.get("type") == "url_verification":
        return {"challenge": body.get("challenge")}

    # 处理消息
    if body.get("event", {}).get("type") == "message":
        text = body["event"]["text"][""]

        # 解析 TTS 命令
        if text.startswith("/tts "):
            tts_text = text.split(" ", 1)[1]

            # 调用 TTS 服务
            tts_res = requests.post(
                "http://localhost:8000/tts",
                json={"text": tts_text}
            )

            # 发送回飞书
            # ... 实现飞书消息发送

    return {"code": 0}
```

#### 5. 使用方法

在飞书群中：
```
@机器人 /tts 你好，世界
```

---

## 钉钉机器人

### 方案概述

钉钉支持自定义机器人 Webhook，可以被动接收消息。

### 实现步骤

#### 1. 创建钉钉机器人

1. 在钉钉群中添加自定义机器人
2. 安全设置选择「加签」或「关键词」
3. 复制 Webhook 地址

#### 2. 部署接收服务

```python
from fastapi import FastAPI, Request
import requests

app = FastAPI()

@app.post("/dingtalk/webhook")
async def dingtalk_webhook(request: Request):
    body = await request.json()
    text = body.get("text", {}).get("content", "")

    # 处理 TTS 命令
    if text.startswith("/tts "):
        tts_text = text.split(" ", 1)[1]

        # 调用 TTS 服务
        tts_res = requests.post(
            "http://localhost:8000/tts",
            json={"text": tts_text}
        )

        # 发送回钉钉
        # ... 实现钉钉消息发送

    return {"msg": "success"}
```

#### 3. 使用方法

在钉钉群中：
```
/tts 你好，世界
```

---

## 微信机器人

注意：微信个人机器人协议不合规，建议使用公众号/企业微信。

### 企业微信

1. 创建企业微信应用
2. 配置接收消息回调
3. 处理消息并调用 TTS 服务

---

## Telegram Bot

### 实现步骤

#### 1. 创建 Bot

1. 与 @BotFather 对话
2. 发送 `/newbot` 创建机器人
3. 获取 Bot Token

#### 2. 部署 Bot 服务

```python
from fastapi import FastAPI, Request
import requests

BOT_TOKEN = "your-bot-token"
app = FastAPI()

@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    body = await request.json()
    message = body.get("message", {})
    text = message.get("text", "")

    # 处理 /tts 命令
    if text.startswith("/tts "):
        tts_text = text.split(" ", 1)[1]
        chat_id = message["chat"]["id"]

        # 调用 TTS 服务
        tts_res = requests.post(
            "http://localhost:8000/tts",
            json={"text": tts_text}
        )

        # 发送音频文件
        files = {"audio": tts_res.content}
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio",
            data={"chat_id": chat_id},
            files=files
        )

    return {"ok": True}

# 设置 Webhook
# https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-domain.com/<TOKEN>
```

#### 3. 使用方法

在 Telegram 中：
```
/tts 你好，世界
```

---

## Web 应用

### HTML + JavaScript

```html
<!DOCTYPE html>
<html>
<head>
    <title>TTS Demo</title>
</head>
<body>
    <input type="text" id="text" placeholder="输入文本">
    <button onclick="speak()">生成语音</button>
    <audio id="audio" controls></audio>

    <script>
        async function speak() {
            const text = document.getElementById('text').value;
            const response = await fetch('http://localhost:8000/tts', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text})
            });
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            document.getElementById('audio').src = audioUrl;
        }
    </script>
</body>
</html>
```

### React

```jsx
import React, { useState } from 'react';

function TTSComponent() {
    const [text, setText] = useState('');
    const [audioUrl, setAudioUrl] = useState(null);

    const speak = async () => {
        const response = await fetch('http://localhost:8000/tts', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text})
        });
        const audioBlob = await response.blob();
        setAudioUrl(URL.createObjectURL(audioBlob));
    };

    return (
        <div>
            <input value={text} onChange={(e) => setText(e.target.value)} />
            <button onClick={speak}>生成语音</button>
            {audioUrl && <audio src={audioUrl} controls />}
        </div>
    );
}
```

---

## 移动应用

### Flutter

```dart
Future<void> speak(String text) async {
  final response = await http.post(
    Uri.parse('http://your-server.com/tts'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'text': text}),
  );

  if (response.statusCode == 200) {
    // 使用 audioplayers 包播放
    final bytes = response.bodyBytes;
    // ... 播放音频
  }
}
```

### React Native

```javascript
import AudioRecorderPlayer from 'react-native-audio-recorder-player';

const speak = async (text) => {
  const response = await fetch('http://your-server.com/tts', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text}),
  });

  const audioBlob = await response.blob();
  // 使用 react-native-sound 或其他库播放
};
```

### Swift (iOS)

```swift
func speak(text: String) {
    guard let url = URL(string: "http://your-server.com/tts") else { return }

    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.httpBody = try? JSONSerialization.data(withJSONObject: ["text": text])

    URLSession.shared.dataTask(with: request) { data, _, _ in
        if let data = data {
            // 使用 AVAudioPlayer 播放
        }
    }.resume()
}
```

### Kotlin (Android)

```kotlin
fun speak(text: String) {
    val url = URL("http://your-server.com/tts")
    val connection = url.openConnection() as HttpURLConnection
    connection.requestMethod = "POST"
    connection.setRequestProperty("Content-Type", "application/json")

    val body = JSONObject().put("text", text).toString()
    connection.outputStream.use { it.write(body.toByteArray()) }

    // 使用 MediaPlayer 播放响应
}
```

---

## 其他集成方式

### CLI 工具

```bash
#!/bin/bash
tts() {
    text="$*"
    curl -X POST http://localhost:8000/tts \
        -H "Content-Type: application/json" \
        -d "{\"text\":\"$text\"}" \
        --output /tmp/speech.mp3
    afplay /tmp/speech.mp3  # macOS
    # or mpg123 /tmp/speech.mp3  # Linux
}
```

### Home Assistant

```yaml
# configuration.yaml
rest_command:
  tts_speak:
    url: http://localhost:8000/tts
    method: POST
    content_type: "application/json"
    payload: '{"text": "{{ text }}" }'

automation:
  - alias: "TTS Announcement"
    trigger:
      - platform: state
        entity_id: input_boolean.tts_enabled
    action:
      - service: rest_command.tts_speak
        data:
          text: "Hello, Home Assistant"
```
