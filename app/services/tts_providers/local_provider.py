"""
Local TTS Provider - Offline Fallback

This module provides a local TTS provider using pyttsx3 as an offline fallback option.
This provider will be used when all other providers fail.
"""
import asyncio
import logging
import os
import tempfile
from typing import List

import pyttsx3

from app.services.tts_providers.base import TTSProvider, TTSResult, TTSProviderError

logger = logging.getLogger(__name__)


class LocalTTSProvider(TTSProvider):
    """Local TTS provider using pyttsx3

    This provider uses the pyttsx3 library to generate speech locally.
    It serves as an offline fallback when other providers are unavailable.

    Attributes:
        _driver: The pyttsx3 engine driver (lazy initialization)
        _voices_cache: Cached list of available voices
    """

    def __init__(self):
        self._driver = None
        self._voices_cache = None

    @property
    def is_free(self) -> bool:
        """Whether this provider is free to use

        Local TTS is completely free and works offline.
        """
        return True

    @property
    def priority(self) -> int:
        """Provider priority for fallback selection

        Local TTS has lowest priority (3) as it's a fallback option.
        Higher number = lower priority.
        """
        return 3

    def _get_driver(self):
        """Get pyttsx3 driver (lazy initialization)

        Returns:
            The pyttsx3 engine instance

        Raises:
            TTSProviderError: If driver initialization fails
        """
        if self._driver is None:
            try:
                self._driver = pyttsx3.init()
                logger.info("Local TTS driver initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize local TTS driver: {e}")
                raise TTSProviderError(f"初始化本地 TTS 失败: {e}") from e
        return self._driver

    async def text_to_speech(
        self,
        text: str,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> TTSResult:
        """Convert text to speech using pyttsx3

        Args:
            text: The text to convert to speech
            voice: Voice ID to use for synthesis (ignored by pyttsx3)
            rate: Speaking rate adjustment (partially supported)
            pitch: Pitch adjustment (not supported by pyttsx3)
            volume: Volume adjustment (supported)

        Returns:
            TTSResult containing audio data in WAV format

        Raises:
            TTSProviderError: If TTS generation fails or text is empty
        """
        if not text or not text.strip():
            raise TTSProviderError("Text cannot be empty")

        try:
            # Run synchronous generation in thread pool
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._generate_sync,
                text,
                rate,
                volume
            )

            logger.info(
                f"Local TTS generated: text_length={len(text)}, "
                f"audio_size={len(audio_data)}"
            )

            return TTSResult(
                audio_data=audio_data,
                format="wav",
                provider="local",
                cached=False
            )

        except TTSProviderError:
            raise
        except Exception as e:
            logger.error(f"Local TTS generation failed: {e}")
            raise TTSProviderError(f"本地 TTS 生成失败: {e}") from e

    def _generate_sync(
        self,
        text: str,
        rate: str = "+0%",
        volume: str = "+0%"
    ) -> bytes:
        """Synchronously generate audio data

        Args:
            text: The text to convert to speech
            rate: Speaking rate adjustment
            volume: Volume adjustment

        Returns:
            Audio data as bytes in WAV format

        Raises:
            TTSProviderError: If audio generation fails
        """
        driver = self._get_driver()

        # Try to set Chinese voice if available
        try:
            voices = driver.getProperty('voices')
            chinese_voice = None

            # Look for Chinese voice
            for voice in voices:
                if 'zh' in voice.id.lower() or 'chinese' in voice.name.lower():
                    chinese_voice = voice
                    break

            if chinese_voice:
                driver.setProperty('voice', chinese_voice.id)
                logger.info(f"Using Chinese voice: {chinese_voice.name}")
            else:
                logger.warning("No Chinese voice found, using default voice")

        except Exception as e:
            logger.warning(f"Failed to set Chinese voice: {e}")

        # Set rate if provided
        try:
            if rate != "+0%":
                current_rate = driver.getProperty('rate')
                # Parse rate like "+10%" or "-20%"
                rate_percent = int(rate.strip('%'))
                new_rate = int(current_rate * (1 + rate_percent / 100))
                driver.setProperty('rate', new_rate)
        except Exception as e:
            logger.warning(f"Failed to set rate: {e}")

        # Set volume if provided
        try:
            if volume != "+0%":
                current_volume = driver.getProperty('volume')
                # Parse volume like "+10%" or "-50%"
                volume_percent = int(volume.strip('%'))
                new_volume = max(0.0, min(1.0, current_volume * (1 + volume_percent / 100)))
                driver.setProperty('volume', new_volume)
        except Exception as e:
            logger.warning(f"Failed to set volume: {e}")

        # Save to temporary file
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='wb',
                suffix='.wav',
                delete=False
            ) as temp_file:
                temp_path = temp_file.name

            # Generate speech to file
            driver.save_to_file(text, temp_path)
            driver.runAndWait()

            # Read the generated audio file
            if not os.path.exists(temp_path):
                raise TTSProviderError("Audio file was not created")

            with open(temp_path, 'rb') as f:
                audio_data = f.read()

            # Verify WAV file header
            if len(audio_data) < 4 or audio_data[:4] != b"RIFF":
                logger.warning("Generated audio is not a valid WAV file")
                # Still return the data, might be playable

            return audio_data

        except Exception as e:
            logger.error(f"Failed to generate audio file: {e}")
            raise TTSProviderError(f"音频文件生成失败: {e}") from e
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file {temp_path}: {e}")

    async def get_available_voices(self) -> List[dict]:
        """Get list of available voices

        Returns:
            List of voice dictionaries containing voice metadata

        Raises:
            TTSProviderError: If voice retrieval fails
        """
        if self._voices_cache is not None:
            return self._voices_cache.copy()

        try:
            loop = asyncio.get_event_loop()
            voices = await loop.run_in_executor(None, self._get_voices_sync)
            self._voices_cache = voices
            return voices.copy()

        except Exception as e:
            logger.error(f"Failed to get available voices: {e}")
            raise TTSProviderError(f"获取音色列表失败: {e}") from e

    def _get_voices_sync(self) -> List[dict]:
        """Synchronously get available voices

        Returns:
            List of voice dictionaries
        """
        driver = self._get_driver()
        voices_list = []

        try:
            pyttsx_voices = driver.getProperty('voices')

            for voice in pyttsx_voices:
                voice_dict = {
                    "id": voice.id,
                    "name": voice.name,
                    "language": self._extract_language(voice),
                    "gender": "Unknown",
                    "provider": "local"
                }
                voices_list.append(voice_dict)

            logger.info(f"Found {len(voices_list)} local voices")

            # If no voices found, add a default fallback
            if not voices_list:
                voices_list.append({
                    "id": "default",
                    "name": "Default Voice",
                    "language": "unknown",
                    "gender": "Unknown",
                    "provider": "local"
                })

        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            # Return default voice on error
            return [{
                "id": "default",
                "name": "Default Voice",
                "language": "unknown",
                "gender": "Unknown",
                "provider": "local"
            }]

        return voices_list

    def _extract_language(self, voice) -> str:
        """Extract language code from voice object

        Args:
            voice: pyttsx3 voice object

        Returns:
            Language code string
        """
        try:
            voice_id = voice.id.lower()
            voice_name = voice.name.lower()

            # Check for Chinese
            if 'zh' in voice_id or 'chinese' in voice_name:
                return 'zh-CN'
            # Check for English
            if 'en' in voice_id or 'english' in voice_name:
                return 'en-US'
            # Check for other common languages
            if 'es' in voice_id or 'spanish' in voice_name:
                return 'es-ES'
            if 'fr' in voice_id or 'french' in voice_name:
                return 'fr-FR'
            if 'de' in voice_id or 'german' in voice_name:
                return 'de-DE'

            return 'unknown'
        except Exception:
            return 'unknown'
