"""
Edge TTS 服务封装
"""
import edge_tts
import asyncio
import logging
from typing import AsyncIterator, Optional
import io

logger = logging.getLogger(__name__)


class EdgeTTSService:
    """Edge TTS 服务类"""

    def __init__(self):
        self._voices_cache: Optional[list] = None

    async def text_to_speech(
        self,
        text: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> bytes:
        """
        将文本转换为语音

        Args:
            text: 要转换的文本
            voice: 音色 ID
            rate: 语速
            pitch: 音调
            volume: 音量

        Returns:
            音频数据 (bytes)
        """
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )

            # 收集音频数据
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
                elif chunk["type"] == "WordBoundary":
                    # 可用于实现字幕或进度跟踪
                    pass

            logger.info(f"成功生成语音: {len(text)} 字符, {len(audio_data)} 字节")
            return audio_data

        except Exception as e:
            logger.error(f"TTS 生成失败: {e}")
            raise

    async def text_to_speech_stream(
        self,
        text: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> AsyncIterator[bytes]:
        """
        流式输出语音数据

        Args:
            text: 要转换的文本
            voice: 音色 ID
            rate: 语速
            pitch: 音调
            volume: 音量

        Yields:
            音频数据块
        """
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]

        except Exception as e:
            logger.error(f"流式 TTS 生成失败: {e}")
            raise

    async def list_voices(self, use_cache: bool = True) -> list:
        """
        获取所有可用音色

        Args:
            use_cache: 是否使用缓存

        Returns:
            音色列表
        """
        if use_cache and self._voices_cache:
            return self._voices_cache

        try:
            voices = await edge_tts.list_voices()
            self._voices_cache = voices
            return voices

        except Exception as e:
            logger.error(f"获取音色列表失败: {e}")
            raise

    async def get_chinese_voices(self) -> list:
        """获取中文音色列表"""
        all_voices = await self.list_voices()
        return [v for v in all_voices if v.get("Locale", "").startswith("zh-")]

    async def get_english_voices(self) -> list:
        """获取英文音色列表"""
        all_voices = await self.list_voices()
        return [v for v in all_voices if v.get("Locale", "").startswith("en-")]


# 全局实例
tts_service = EdgeTTSService()
