"""
TTS 路由 - 文本转语音接口
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
import logging

import io

from app.models.schemas import TTSRequest
from app.services.edge_tts import tts_service
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("")
async def text_to_speech(request: Request, req: TTSRequest):
    """
    文本转语音

    将输入的文本转换为语音音频并返回。

    - **text**: 要转换的文本（必填）
    - **voice**: 音色 ID，可使用简称如 xiaoxiao, yunyang（可选）
    - **rate**: 语速，例如: +10%, -20%（可选，默认 +0%）
    - **pitch**: 音调，例如: +10Hz, -5Hz（可选，默认 +0Hz）
    - **volume**: 音量，例如: +10%, -50%（可选，默认 +0%）
    """
    try:
        # 使用默认音色
        voice = req.voice or settings.DEFAULT_VOICE

        logger.info(f"TTS 请求: text='{req.text[:50]}...', voice={voice}")

        # 生成语音
        audio_data = await tts_service.text_to_speech(
            text=req.text,
            voice=voice,
            rate=req.rate,
            pitch=req.pitch,
            volume=req.volume
        )

        # 返回音频流
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=speech.mp3",
                "Content-Length": str(len(audio_data)),
                "X-Voice-Used": voice,
                "Access-Control-Expose-Headers": "X-Voice-Used,Content-Length"
            }
        )

    except Exception as e:
        logger.error(f"TTS 生成失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"语音生成失败: {str(e)}"
        )


@router.get("/test")
async def test_tts():
    """
    测试端点 - 返回一个简单的测试音频

    用于快速验证服务是否正常工作。
    """
    try:
        audio_data = await tts_service.text_to_speech(
            text="你好，Edge TTS 服务运行正常！",
            voice="zh-CN-XiaoxiaoNeural"
        )

        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"测试失败: {str(e)}"
        )
