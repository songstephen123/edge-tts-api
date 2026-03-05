"""
TTS 路由 - 文本转语音接口
支持 Opus 格式输出（优化版：opusenc + 流式处理）
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
import logging
import os
import uuid
from datetime import datetime

from app.models.schemas import TTSRequest
from app.services.edge_tts import tts_service
from app.services.opus_converter import (
    convert_to_opus_streaming_fast,
    convert_to_opus_with_cache,
    get_performance_stats
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# 静态文件存储目录
STATIC_DIR = "/tmp/tts_audio"
os.makedirs(STATIC_DIR, exist_ok=True)


async def convert_to_opus(mp3_data: bytes) -> bytes:
    """
    使用 ffmpeg 将 MP3 转换为 Opus

    Args:
        mp3_data: MP3 格式的音频数据

    Returns:
        Opus 格式的音频数据
    """
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as mp3_file:
            mp3_file.write(mp3_data)
            mp3_path = mp3_file.name

        opus_path = mp3_path.replace(".mp3", ".opus")

        # 使用 ffmpeg 转换
        # -acodec libopus: 使用 opus 编码器
        # -b:a 64k: 比特率 64kbps（Opus 推荐）
        # -vn: 不包含视频
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i", mp3_path,
            "-acodec", "libopus",
            "-b:a", "64k",
            "-vn",
            opus_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.error(f"FFmpeg 转换失败: {stderr.decode()}")
            # 如果转换失败，返回原 MP3
            return mp3_data

        # 读取 Opus 文件
        with open(opus_path, "rb") as f:
            opus_data = f.read()

        # 清理临时文件
        os.unlink(mp3_path)
        os.unlink(opus_path)

        return opus_data

    except Exception as e:
        logger.error(f"Opus 转换失败: {e}")
        # 转换失败时返回原 MP3
        return mp3_data


async def save_audio_file(audio_data: bytes, format: str = "mp3") -> str:
    """
    保存音频文件到静态目录

    Args:
        audio_data: 音频数据
        format: 格式 (mp3/opus)

    Returns:
        文件名（可通过 URL 访问）
    """
    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    ext = format.lower()
    filename = f"{file_id}.{ext}"
    filepath = os.path.join(STATIC_DIR, filename)

    # 保存文件
    with open(filepath, "wb") as f:
        f.write(audio_data)

    logger.info(f"音频文件已保存: {filename}")

    return filename


@router.post("")
async def text_to_speech(req: TTSRequest):
    """
    文本转语音（优化版：opusenc + 流式处理）

    支持多种输出格式：
    - mp3: 默认格式
    - opus: 飞书推荐格式（使用 opusenc 快速转换）

    - **text**: 要转换的文本（必填）
    - **voice**: 音色 ID 或简称（可选）
    - **rate**: 语速（可选）
    - **format**: 输出格式，支持 mp3/opus（可选，默认 mp3）
    """
    try:
        # 获取输出格式
        output_format = getattr(req, 'format', 'mp3')
        if output_format not in ['mp3', 'opus']:
            output_format = 'mp3'

        # 使用默认音色
        voice = req.voice or settings.DEFAULT_VOICE

        logger.info(f"TTS 请求: text='{req.text[:50]}...', voice={voice}, format={output_format}")

        # 生成语音（默认 MP3）
        mp3_data = await tts_service.text_to_speech(
            text=req.text,
            voice=voice,
            rate=getattr(req, 'rate', '+0%'),
            pitch=getattr(req, 'pitch', '+0Hz'),
            volume=getattr(req, 'volume', '+0%')
        )

        # 如果需要 Opus 格式，使用优化转换器
        if output_format == 'opus':
            audio_data = await convert_to_opus_with_cache(
                mp3_data,
                text=req.text,
                voice=voice
            )
        else:
            audio_data = mp3_data

        # 保存音频文件
        filename = await save_audio_file(audio_data, output_format)

        # 返回音频流
        media_type = "audio/opus" if output_format == 'opus' else "audio/mpeg"

        return StreamingResponse(
            asyncio.BytesIO(audio_data),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(audio_data)),
                "X-Audio-Filename": filename,
                "X-Audio-Format": output_format,
                "Access-Control-Expose-Headers": "X-Audio-Filename,X-Audio-Format,Content-Length"
            }
        )

    except Exception as e:
        logger.error(f"TTS 生成失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"语音生成失败: {str(e)}"
        )


@router.post("/url")
async def text_to_speech_url(req: TTSRequest):
    """
    文本转语音 - 返回 URL 格式

    返回 JSON 包含音频 URL，飞书可以直接访问

    响应格式：
    {
      "success": true,
      "url": "http://server:8000/static/audio/xxx.opus",
      "filename": "xxx.opus",
      "format": "opus",
      "text": "原始文本"
    }
    """
    try:
        output_format = getattr(req, 'format', 'opus')  # 默认 opus
        if output_format not in ['mp3', 'opus']:
            output_format = 'opus'

        voice = req.voice or settings.DEFAULT_VOICE

        logger.info(f"TTS URL 请求: text='{req.text[:50]}...', voice={voice}, format={output_format}")

        # 生成语音
        audio_data = await tts_service.text_to_speech(
            text=req.text,
            voice=voice,
            rate=getattr(req, 'rate', '+0%'),
            pitch=getattr(req, 'pitch', '+0Hz'),
            volume=getattr(req, 'volume', '+0%')
        )

        # 转换为 Opus（如果需要）
        if output_format == 'opus':
            audio_data = await convert_to_opus(audio_data)

        # 保存文件
        filename = await save_audio_file(audio_data, output_format)

        # 生成访问 URL
        # 注意：需要将 localhost 替换为实际服务器 IP
        audio_url = f"http://115.190.252.250:8000/static/audio/{filename}"

        return {
            "success": True,
            "url": audio_url,
            "filename": filename,
            "format": output_format,
            "text": req.text,
            "text_length": len(req.text),
            "voice_used": voice
        }

    except Exception as e:
        logger.error(f"TTS URL 生成失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"语音 URL 生成失败: {str(e)}"
        )


@router.post("/test")
async def test_tts():
    """测试端点 - 返回一个简单的测试音频"""
    try:
        mp3_data = await tts_service.text_to_speech(
            text="你好，Edge TTS 服务运行正常！",
            voice="zh-CN-XiaoxiaoNeural"
        )

        # 转换为 Opus（使用优化转换器）
        opus_data = await convert_to_opus_with_cache(
            mp3_data,
            text="你好，Edge TTS 服务运行正常！",
            voice="zh-CN-XiaoxiaoNeural"
        )

        return StreamingResponse(
            asyncio.BytesIO(opus_data),
            media_type="audio/opus"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"测试失败: {str(e)}"
        )


@router.get("/performance")
async def get_performance():
    """获取转换性能统计"""
    return get_performance_stats()


@router.post("/feishu")
async def feishu_tts(req: TTSRequest):
    """
    飞书专用接口（优化版：opusenc + 流式处理 + 缓存）

    返回飞书可直接使用的音频 URL 和格式

    响应格式：
    {
      "success": true,
      "audio_url": "http://server:8000/static/audio/xxx.opus",
      "audio_key": "xxx.opus",
      "duration": 2500,
      "text": "原始文本",
      "cached": false
    }
    """
    try:
        # 默认使用 Opus 格式（飞书推荐）
        output_format = 'opus'
        voice = req.voice or settings.DEFAULT_VOICE

        logger.info(f"飞书 TTS 请求: text='{req.text[:50]}...', voice={voice}")

        # 生成语音（MP3）
        mp3_data = await tts_service.text_to_speech(
            text=req.text,
            voice=voice,
            rate=getattr(req, 'rate', '+0%'),
            pitch=getattr(req, 'pitch', '+0Hz'),
            volume=getattr(req, 'volume', '+0%')
        )

        # 使用优化转换器转换为 Opus（带缓存）
        opus_data = await convert_to_opus_with_cache(
            mp3_data,
            text=req.text,
            voice=voice
        )

        # 保存文件
        filename = await save_audio_file(opus_data, 'opus')

        # 估算音频时长（Opus 约 32kbps）
        duration_ms = len(opus_data) * 8 // 32

        # 检查是否来自缓存
        import hashlib
        cache_key = hashlib.md5(f"{req.text}:{voice}".encode()).hexdigest()
        is_cached = os.path.exists(f"/tmp/tts_cache/{cache_key}.opus")

        # 返回飞书格式
        return {
            "success": True,
            "audio_url": f"http://115.190.252.250:8000/static/audio/{filename}",
            "audio_key": filename,
            "duration": duration_ms,
            "text": req.text,
            "text_length": len(req.text),
            "voice_used": voice,
            "cached": is_cached,
            "format": "opus"
        }

    except Exception as e:
        logger.error(f"飞书 TTS 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"飞书语音生成失败: {str(e)}"
        )
