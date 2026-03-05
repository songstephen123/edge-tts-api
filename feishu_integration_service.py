"""
飞书 x Edge TTS 集成服务
复用您已有的飞书企业应用，添加 TTS 功能
"""
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import requests
import logging
import os
from typing import Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Feishu TTS Integration")

# ============ 配置区 ============
# 从环境变量读取配置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")
FEISHU_ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "")

# 您的 TTS 服务地址
TTS_API_URL = os.getenv("TTS_API_URL", "http://localhost:8000/tts")

# 飞书 API 地址
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"


# ============ 飞书 API 工具 ============
class FeishuClient:
    """飞书 API 客户端"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._access_token: Optional[str] = None

    def get_tenant_access_token(self) -> str:
        """获取 tenant_access_token"""
        if self._access_token:
            return self._access_token

        url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
        response = requests.post(url, json={
            "app_id": self.app_id,
            "app_secret": self.app_secret
        })

        if response.status_code != 200:
            raise Exception(f"获取 token 失败: {response.text}")

        data = response.json()
        if data.get("code") != 0:
            raise Exception(f"获取 token 失败: {data}")

        self._access_token = data.get("tenant_access_token")
        return self._access_token

    def send_text_message(self, chat_id: str, text: str):
        """发送文本消息"""
        token = self.get_tenant_access_token()

        url = f"{FEISHU_API_BASE}/im/v1/messages?receive_id_type=chat_id"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json={
            "receive_id": chat_id,
            "msg_type": "text",
            "content": "{\"text\":\"" + text + "\"}"
        })

        return response.json()

    def send_audio_message(self, chat_id: str, audio_url: str, duration: int = 0):
        """发送音频消息"""
        token = self.get_tenant_access_token()

        url = f"{FEISHY_API_BASE}/im/v1/messages?receive_id_type=chat_id"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json={
            "receive_id": chat_id,
            "msg_type": "audio",
            "content": f"{{\"audio_key\":\"{audio_url}\",\"duration\":{duration}}}"
        })

        return response.json()

    def upload_file(self, file_path: str, file_type: str = "audio") -> str:
        """上传文件到飞书"""
        token = self.get_tenant_access_token()

        # 1. 获取上传地址
        url = f"{FEISHY_API_BASE}/drive/v1/files/upload_all"
        headers = {"Authorization": f"Bearer {token}"}

        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"file_type": file_type}
            response = requests.post(url, headers=headers, files=files, data=data)

        upload_data = response.json()
        if upload_data.get("code") != 0:
            raise Exception(f"上传文件失败: {upload_data}")

        return upload_data.get("file_key")


# 全局飞书客户端（稍后初始化）
feishu_client: Optional[FeishuClient] = None


# ============ TTS 服务 ============
def generate_speech(text: str, voice: str = "xiaoxiao") -> bytes:
    """调用 TTS API 生成语音"""
    response = requests.post(TTS_API_URL, json={
        "text": text,
        "voice": voice
    })

    if response.status_code != 200:
        raise Exception(f"TTS 调用失败: {response.status_code}")

    return response.content


# ============ Webhook 端点 ============
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Feishu TTS Integration",
        "status": "running",
        "endpoints": {
            "/webhook/feishu": "飞书事件接收地址"
        }
    }


@app.post("/webhook/feishu")
async def feishu_webhook(request: Request):
    """飞书事件 Webhook"""
    global feishu_client

    body = await request.json()
    logger.info(f"收到飞书事件: {body}")

    # URL 验证（首次配置时）
    if body.get("type") == "url_verification":
        logger.info("URL 验证请求")
        return JSONResponse(content={"challenge": body.get("challenge")})

    # 初始化飞书客户端
    if not feishu_client:
        if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
            logger.error("飞书应用凭证未配置")
            return JSONResponse(
                status_code=500,
                content={"code": -1, "msg": "飞书应用凭证未配置"}
            )

        feishu_client = FeishuClient(FEISHU_APP_ID, FEISHU_APP_SECRET)

    # 处理消息事件
    if body.get("type") == "event" and body.get("event", {}).get("type") == "message":
        event = body.get("event", {})

        # 获取消息内容
        content = event.get("content", {})
        message_type = content.get("message_type")

        # 只处理文本消息
        if message_type != "text":
            return JSONResponse(content={"code": 0, "msg": "success"})

        # 解析文本内容
        import json
        try:
            text_content = json.loads(content)
            text = text_content.get("text", "").strip()
        except:
            return JSONResponse(content={"code": 0, "msg": "success"})

        # 获取会话 ID
        chat_id = event.get("chat_id", "")
        open_chat_id = event.get("open_chat_id", "")

        logger.info(f"收到消息: {text}, chat_id: {chat_id}")

        # 检查是否是 TTS 命令
        if text.startswith("/tts ") or text.startswith("/语音 "):
            # 提取要转换的文本
            tts_text = text.split(" ", 1)[1] if " " in text else text.replace("/tts", "").replace("/语音", "").strip()

            if not tts_text:
                # 发送帮助消息
                feishu_client.send_text_message(
                    open_chat_id,
                    "🎙️ 使用方法：\n/tts 你要转换的文字\n\n示例：/tts 你好，世界"
                )
                return JSONResponse(content={"code": 0, "msg": "success"})

            try:
                # 异步处理 TTS 请求
                import asyncio
                asyncio.create_task(process_tts_request(open_chat_id, tts_text))

            except Exception as e:
                logger.error(f"TTS 处理失败: {e}")
                feishu_client.send_text_message(
                    open_chat_id,
                    f"❌ 语音生成失败: {str(e)}"
                )

    return JSONResponse(content={"code": 0, "msg": "success"})


async def process_tts_request(chat_id: str, text: str):
    """异步处理 TTS 请求"""
    try:
        logger.info(f"开始生成语音: {text}")

        # 调用 TTS API (飞书专用端点，返回 Opus 格式和 URL)
        tts_response = requests.post(
            f"{TTS_API_URL}/feishu",
            json={"text": text}
        )

        if tts_response.status_code != 200:
            raise Exception(f"TTS API 调用失败: {tts_response.status_code}")

        result = tts_response.json()

        if not result.get("success"):
            raise Exception(f"TTS 生成失败: {result}")

        audio_url = result.get("audio_url")
        audio_key = result.get("audio_key")
        duration = result.get("duration", 0)

        # 发送卡片消息到飞书（包含音频信息）
        # 注意：飞书需要上传音频文件或使用特定的音频消息格式
        # 这里先发送文本消息，包含音频 URL
        card_content = {
            "config": {
                "wide_screen_mode": True
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"🔊 语音已生成\n\n文本: {text}\n\n格式: Opus\n时长: {duration//1000}秒",
                        "tag": "lark_md"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "content": "播放音频"
                            },
                            "type": "default",
                            "url": audio_url
                        }
                    ]
                }
            ]
        }

        # 发送卡片消息
        send_card_url = f"{FEISHU_API_BASE}/im/v1/messages?receive_id_type=chat_id"
        headers = {
            "Authorization": f"Bearer {feishu_client.get_tenant_access_token()}",
            "Content-Type": "application/json"
        }

        card_response = requests.post(
            send_card_url,
            headers=headers,
            json={
                "receive_id": chat_id,
                "msg_type": "interactive",
                "content": json.dumps(card_content)
            }
        )

        logger.info(f"飞书消息已发送: {card_response.json()}")

    except Exception as e:
        logger.error(f"处理 TTS 请求失败: {e}", exc_info=True)
        feishu_client.send_text_message(
            chat_id,
            f"❌ 语音生成失败: {str(e)}"
        )


# ============ 配置端点 ============
@app.get("/config")
async def get_config():
    """获取当前配置"""
    return {
        "feishu_app_id": FEISHU_APP_ID[:10] + "..." if FEISHU_APP_ID else None,
        "feishu_configured": bool(FEISHU_APP_ID and FEISHU_APP_SECRET),
        "tts_api_url": TTS_API_URL,
        "needs_config": not bool(FEISHU_APP_ID and FEISHU_APP_SECRET)
    }


@app.post("/config")
async def set_config(config: dict):
    """动态设置配置"""
    global feishu_client

    app_id = config.get("app_id")
    app_secret = config.get("app_secret")

    if app_id and app_secret:
        os.environ["FEISHU_APP_ID"] = app_id
        os.environ["FEISHU_APP_SECRET"] = app_secret

        FEISHU_APP_ID = app_id
        FEISHU_APP_SECRET = app_secret

        # 重新初始化客户端
        feishu_client = FeishuClient(app_id, app_secret)

        return {"success": True, "message": "配置已更新"}

    return {"success": False, "message": "请提供 app_id 和 app_secret"}


# ============ 启动服务 ============
if __name__ == "__main__":
    import uvicorn

    # 初始化飞书客户端
    if FEISHU_APP_ID and FEISHU_APP_SECRET:
        feishu_client = FeishuClient(FEISHU_APP_ID, FEISHY_APP_SECRET)
        logger.info("飞书客户端已初始化")
    else:
        logger.warning("⚠️  飞书应用凭证未配置，请通过 /config 端点配置")

    # 启动服务
    uvicorn.run(app, host="0.0.0.0", port=8001)
