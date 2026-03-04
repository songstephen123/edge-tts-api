"""
钉钉机器人集成示例
演示如何在钉钉机器人中调用 Edge TTS Service
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import hmac
import hashlib
import base64
import urllib.parse
import time
import os

# 配置
TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL", "http://localhost:8000")
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK", "")
DINGTALK_SECRET = os.getenv("DINGTALK_SECRET", "")

app = FastAPI()


@app.post("/dingtalk/webhook")
async def dingtalk_webhook(request: Request):
    """
    钉钉机器人 Webhook 接收端

    钉钉配置:
    1. 打开钉钉开放平台
    2. 创建机器人应用
    3. 配置消息接收地址
    """
    body = await request.json()

    # 验证签名（如果启用了加签）
    if DINGTALK_SECRET:
        # 实现签名验证
        pass

    # 处理消息
    text = body.get("text", {}).get("content", "")

    # 检查是否是 TTS 请求
    if text.startswith("/tts ") or text.startswith("/语音 "):
        tts_text = text.split(" ", 1)[1] if " " in text else "你好"

        # 调用 TTS 服务
        try:
            tts_response = requests.post(
                f"{TTS_SERVICE_URL}/tts",
                json={"text": tts_text},
                timeout=30
            )

            if tts_response.status_code == 200:
                # 返回音频文件链接
                audio_url = f"{TTS_SERVICE_URL}/static/tts_{hash(tts_text)}.mp3"

                # 发送钉钉消息
                send_dingtalk_message(f"语音已生成: {audio_url}")

            else:
                send_dingtalk_message(f"语音生成失败")

        except Exception as e:
            send_dingtalk_message(f"服务错误: {str(e)}")

    return JSONResponse(content={"msg": "success"})


def send_dingtalk_message(content: str):
    """
    发送消息到钉钉群

    文档: https://open.dingtalk.com/document/robots/custom-robot-access
    """
    if not DINGTALK_WEBHOOK:
        print("未配置钉钉 Webhook")
        return

    # 计算签名（如果启用了加签）
    webhook = DINGTALK_WEBHOOK
    if DINGTALK_SECRET:
        timestamp = str(round(time.time() * 1000))
        secret_enc = DINGTALK_SECRET.encode('utf-8')
        string_to_sign = f'{timestamp}\n{DINGTALK_SECRET}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        webhook = f"{DINGTALK_WEBHOOK}&timestamp={timestamp}&sign={sign}"

    # 发送消息
    data = {
        "msgtype": "text",
        "text": {"content": content}
    }

    requests.post(webhook, json=data)


# 使用说明
"""
钉钉集成步骤：

1. 创建钉钉机器人
   - 在钉钉群中添加自定义机器人
   - 选择安全设置: 加签 (推荐) 或 关键词

2. 获取 Webhook 地址
   - 复制 Webhook 地址到环境变量 DINGTALK_WEBHOOK

3. (可选) 配置加签
   - 复制加签密钥到环境变量 DINGTALK_SECRET

4. 启动服务
   - 设置环境变量后运行此服务

5. 在钉钉群中发送消息:
   /tts 你好，世界
   /语音 这是一条测试消息
"""
