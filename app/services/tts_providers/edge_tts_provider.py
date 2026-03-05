"""
Edge TTS Provider

This module provides a TTS provider implementation using the Microsoft Edge
TTS service via the edge-tts library. It offers free text-to-speech with
a variety of Chinese voices and configurable parameters.
"""
import logging
from typing import Dict, List

import edge_tts

from app.services.tts_providers.base import TTSProvider, TTSResult, TTSProviderError


logger = logging.getLogger(__name__)


class EdgeTTSProvider(TTSProvider):
    """TTS Provider using Microsoft Edge TTS service

    This provider uses the edge-tts library to generate speech using
    Microsoft Edge's free TTS API. It supports multiple Chinese voices
    with configurable rate, pitch, and volume.

    Attributes:
        VOICE_MAP: Dictionary mapping short names to full Edge voice IDs
    """

    # Voice mapping from short names to full Edge TTS voice IDs
    VOICE_MAP: Dict[str, str] = {
        "xiaoxiao": "zh-CN-XiaoxiaoNeural",
        "yunyang": "zh-CN-YunyangNeural",
        "xiaoyi": "zh-CN-XiaoyiNeural",
        "xiaohan": "zh-CN-XiaohanNeural",
        "xiaomeng": "zh-CN-XiaomengNeural",
    }

    # Full voice list with metadata
    _AVAILABLE_VOICES: List[dict] = [
        {
            "id": "zh-CN-XiaoxiaoNeural",
            "name": "Xiaoxiao (Female)",
            "language": "zh-CN",
            "gender": "Female",
            "short_name": "xiaoxiao"
        },
        {
            "id": "zh-CN-YunyangNeural",
            "name": "Yunyang (Male)",
            "language": "zh-CN",
            "gender": "Male",
            "short_name": "yunyang"
        },
        {
            "id": "zh-CN-XiaoyiNeural",
            "name": "Xiaoyi (Female)",
            "language": "zh-CN",
            "gender": "Female",
            "short_name": "xiaoyi"
        },
        {
            "id": "zh-CN-XiaohanNeural",
            "name": "Xiaohan (Female)",
            "language": "zh-CN",
            "gender": "Female",
            "short_name": "xiaohan"
        },
        {
            "id": "zh-CN-XiaomengNeural",
            "name": "Xiaomeng (Female)",
            "language": "zh-CN",
            "gender": "Female",
            "short_name": "xiaomeng"
        },
    ]

    def _resolve_voice(self, voice: str) -> str:
        """Resolve short voice name to full Edge TTS voice ID

        Args:
            voice: Short voice name or full voice ID

        Returns:
            Full Edge TTS voice ID

        Examples:
            >>> provider._resolve_voice("xiaoxiao")
            "zh-CN-XiaoxiaoNeural"
            >>> provider._resolve_voice("zh-CN-XiaoxiaoNeural")
            "zh-CN-XiaoxiaoNeural"
        """
        return self.VOICE_MAP.get(voice, voice)

    async def text_to_speech(
        self,
        text: str,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> TTSResult:
        """Convert text to speech using Edge TTS

        Args:
            text: The text to convert to speech
            voice: Voice ID or short name (e.g., "xiaoxiao")
            rate: Speaking rate adjustment (e.g., "+10%", "-20%")
            pitch: Pitch adjustment (e.g., "+5Hz", "-10Hz")
            volume: Volume adjustment (e.g., "+10%", "-50%")

        Returns:
            TTSResult containing audio data in MP3 format

        Raises:
            TTSProviderError: If TTS generation fails or text is empty
        """
        if not text or not text.strip():
            raise TTSProviderError("Text cannot be empty")

        resolved_voice = self._resolve_voice(voice)

        try:
            # Create communicate object with parameters
            communicate = edge_tts.Communicate(
                text=text,
                voice=resolved_voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )

            # Stream audio data
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])

            if not audio_chunks:
                raise TTSProviderError("No audio data generated")

            # Combine chunks into single bytes object
            audio_data = b"".join(audio_chunks)

            logger.info(
                f"Generated TTS audio: voice={resolved_voice}, "
                f"text_length={len(text)}, audio_size={len(audio_data)}"
            )

            return TTSResult(
                audio_data=audio_data,
                format="mp3",
                provider=self.name,
                cached=False
            )

        except edge_tts.InvalidEdgeTTSError as e:
            logger.error(f"Edge TTS invalid parameter: {e}")
            raise TTSProviderError(f"Invalid TTS parameter: {e}") from e
        except Exception as e:
            logger.error(f"Edge TTS generation failed: {e}")
            raise TTSProviderError(f"TTS generation failed: {e}") from e

    async def get_available_voices(self) -> List[dict]:
        """Get list of available voices

        Returns:
            List of voice dictionaries containing voice metadata including
            id, name, language, gender, and short_name
        """
        return self._AVAILABLE_VOICES.copy()

    @property
    def is_free(self) -> bool:
        """Whether this provider is free to use

        Edge TTS is completely free with no API key required.
        """
        return True

    @property
    def priority(self) -> int:
        """Provider priority for fallback selection

        Edge TTS has high priority (1) because it's free and reliable.
        Lower number = higher priority.
        """
        return 1
