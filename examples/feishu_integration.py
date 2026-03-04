"""
飞书机器人集成示例
演示如何在飞书机器人中调用 Edge TTS Service
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
import hashlib
import hmac
import json
import os

# 配置
TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL", "http://localhost:8000")
FEISHU_VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")
FEISHU_ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "")

app = FastAPI()


@app.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    """
    飞书机器人 Webhook 接收端

    飞书配置:
    1. 打开飞书开放平台
    2. 创建机器人应用
    3. 配置事件订阅，URL 为: https://your-domain.com/feishu/webhook
    4. 填写验证凭证
    """
    body = await request.json()

    # URL 验证（飞书首次配置时触发）
    if body.get("type") == "url_verification":
        return JSONResponse(content={
            "challenge": body.get("challenge")
        })

    # 消息处理
    if body.get("type") == "event" and body.get("event", {}).get("type") == "message":
        event = body.get("event", {})
        message = event.get("text", {}).get("", "")

        # 解析消息内容（去掉 @机器人）
        text = message.replace("_AT_", "").strip()

        # 检查是否是 TTS 请求
        if text.startswith("/tts ") or text.startswith("/语音 "):
            # 提取要转换的文本
            tts_text = text.split(" ", 1)[1] if " " in text else "你好"

            # 调用 TTS 服务
            try:
                tts_response = requests.post(
                    f"{TTS_SERVICE_URL}/tts",
                    json={"text": tts_text},
                    timeout=30
                )

                if tts_response.status_code == 200:
                    # 保存音频文件
                    audio_filename = f"tts_{hash(tts_text)}.mp3"
                    with open(f"static/{audio_filename}", "wb") as f:
                        f.write(tts_response.content)

                    # 构建飞书消息
                    audio_url = f"https://your-domain.com/static/{audio_filename}"

                    # 发送消息回飞书
                    await send_feishu_message(
                        event.get("open_chat_id"),
                        {
                            "msg_type": "audio",
                            "content": {
                                "audio_key": audio_filename,
                                "duration": len(tts_response.content) // 1000  # 估算时长
                            }
                        }
                    )

                else:
                    await send_feishu_message(
                        event.get("open_chat_id"),
                        {
                            "msg_type": "text",
                            "content": {"text": f"语音生成失败: {tts_response.text}"}
                        }
                    )

            except Exception as e:
                await send_feishu_message(
                    event.get("open_chat_id"),
                    {
                        "msg_type": "text",
                        "content": {"text": f"服务错误: {str(e)}"}
                    }
                )

    return JSONResponse(content={"code": 0, "msg": "success"})


async def send_feisho_message(chat_id: str, message: dict):
    """
    发送消息到飞书

    需要使用飞书 API 调用
    文档: https://open.feishu.cn/document/ukTMukTMukTM/uEjNwUjLxYDM14SM2ATN
    """
    # 这里需要实现飞书 API 调用
    # 包括获取 tenant_access_token 和发送消息
    pass


# 使用说明
"""
飞书集成步骤：

1. 创建飞书应用
   - 访问 https://open.feishu.cn/
   - 创建企业自建应用

2. 配置权限
   - 获取 im:message 权限
   - 获取 im:message:group_at_msg 权限

3. 启用事件订阅
   - 配置请求 URL: https://your-domain.com/feishu/webhook
   - 填写验证 Token 和加密 Key

4. 将机器人添加到群组

5. 在群中发送消息:
   /tts 你好，世界
   /语音 这是一条测试消息
"""
