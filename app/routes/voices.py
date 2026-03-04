"""
音色管理路由
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import logging

from app.models.schemas import VoiceInfo, VoicesResponse
from app.services.edge_tts import tts_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=VoicesResponse)
async def list_voices(
    locale: str = Query(None, description="筛选特定语言，例如: zh-CN, en-US"),
    gender: str = Query(None, description="筛选性别: Male, Female")
):
    """
    获取所有可用音色列表

    返回 Edge TTS 支持的所有音色。

    - **locale**: 可选，按语言筛选（如 zh-CN, en-US）
    - **gender**: 可选，按性别筛选（Male, Female）
    """
    try:
        voices = await tts_service.list_voices()

        # 筛选
        if locale:
            voices = [v for v in voices if v.get("Locale", "").lower() == locale.lower()]
        if gender:
            voices = [v for v in voices if v.get("Gender", "").lower() == gender.lower()]

        # 转换为响应模型
        voice_list = [
            VoiceInfo(
                name=v.get("Name", ""),
                id=v.get("Name", ""),
                locale=v.get("Locale", ""),
                locale_name=v.get("LocaleName", ""),
                gender=v.get("Gender", ""),
                description=v.get("Description", "")
            )
            for v in voices
        ]

        return VoicesResponse(voices=voice_list, total=len(voice_list))

    except Exception as e:
        logger.error(f"获取音色列表失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取音色列表失败: {str(e)}"
        )


@router.get("/chinese", response_model=VoicesResponse)
async def list_chinese_voices():
    """
    获取中文音色列表

    返回所有中文（简体/繁体）音色。
    """
    try:
        voices = await tts_service.get_chinese_voices()

        voice_list = [
            VoiceInfo(
                name=v.get("Name", ""),
                id=v.get("Name", ""),
                locale=v.get("Locale", ""),
                locale_name=v.get("LocaleName", ""),
                gender=v.get("Gender", ""),
                description=v.get("Description", "")
            )
            for v in voices
        ]

        return VoicesResponse(voices=voice_list, total=len(voice_list))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取中文音色失败: {str(e)}"
        )


@router.get("/english", response_model=VoicesResponse)
async def list_english_voices():
    """
    获取英文音色列表

    返回所有英文音色。
    """
    try:
        voices = await tts_service.get_english_voices()

        voice_list = [
            VoiceInfo(
                name=v.get("Name", ""),
                id=v.get("Name", ""),
                locale=v.get("Locale", ""),
                locale_name=v.get("LocaleName", ""),
                gender=v.get("Gender", ""),
                description=v.get("Description", "")
            )
            for v in voices
        ]

        return VoicesResponse(voices=voice_list, total=len(voice_list))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取英文音色失败: {str(e)}"
        )


@router.get("/popular")
async def list_popular_voices():
    """
    获取常用音色列表

    返回精选的常用音色，方便快速选择。
    """
    popular_voices = {
        "chinese": [
            {"id": "zh-CN-XiaoxiaoNeural", "name": "晓晓 (女声)", "gender": "Female"},
            {"id": "zh-CN-XiaoyiNeural", "name": "晓伊 (女声)", "gender": "Female"},
            {"id": "zh-CN-YunyangNeural", "name": "云扬 (男声)", "gender": "Male"},
            {"id": "zh-CN-XiaomengNeural", "name": "晓梦 (童声)", "gender": "Female"},
            {"id": "zh-TW-HsiaoChenNeural", "name": "曉臻 (台湾女声)", "gender": "Female"},
        ],
        "english": [
            {"id": "en-US-AriaNeural", "name": "Aria (女声)", "gender": "Female"},
            {"id": "en-US-GuyNeural", "name": "Guy (男声)", "gender": "Male"},
            {"id": "en-GB-SoniaNeural", "name": "Sonia (英式女声)", "gender": "Female"},
        ]
    }

    return popular_voices
