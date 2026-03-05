#!/usr/bin/env python
"""
Test runner for TTS Provider base tests when pytest is not available
"""
import asyncio
import sys
sys.path.insert(0, '/Users/songstephen/edge-tts-skill')

from app.services.tts_providers.base import TTSResult, TTSProviderError, TTSProvider
from typing import List


class MockTTSProvider(TTSProvider):
    """Mock TTS provider for testing"""

    def __init__(self, is_free=True, priority=100):
        self._is_free = is_free
        self._priority = priority
        self._voices = [
            {"id": "mock-voice-1", "name": "Mock Voice 1"},
            {"id": "mock-voice-2", "name": "Mock Voice 2"}
        ]

    @property
    def is_free(self) -> bool:
        return self._is_free

    @property
    def priority(self) -> int:
        return self._priority

    async def text_to_speech(
        self,
        text: str,
        voice: str = "mock-voice-1",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> TTSResult:
        return TTSResult(audio_data=b"mock_audio_data", format="mp3", provider=self.name, cached=False)

    async def get_available_voices(self) -> List[dict]:
        return self._voices


def test_tts_result_creation():
    """Test TTSResult dataclass creation"""
    result = TTSResult(
        audio_data=b"test_audio",
        format="mp3",
        provider="MockProvider",
        cached=True
    )
    assert result.audio_data == b"test_audio"
    assert result.format == "mp3"
    assert result.provider == "MockProvider"
    assert result.cached is True
    print("✓ test_tts_result_creation passed")


async def test_mock_provider_interface():
    """Test mock provider implements interface correctly"""
    provider = MockTTSProvider(is_free=True, priority=100)

    # Test properties
    assert provider.is_free is True
    assert provider.priority == 100
    assert provider.name == "MockTTSProvider"

    # Test text_to_speech
    result = await provider.text_to_speech("Hello, world!")
    assert isinstance(result, TTSResult)
    assert result.audio_data == b"mock_audio_data"
    assert result.format == "mp3"
    assert result.provider == "MockTTSProvider"
    assert result.cached is False

    # Test get_available_voices
    voices = await provider.get_available_voices()
    assert len(voices) == 2
    assert voices[0]["id"] == "mock-voice-1"
    print("✓ test_mock_provider_interface passed")


def test_tts_provider_error():
    """Test TTSProviderError exception"""
    error = TTSProviderError("Test error message")
    assert isinstance(error, Exception)
    assert str(error) == "Test error message"

    try:
        raise TTSProviderError("Test error")
    except TTSProviderError:
        pass
    print("✓ test_tts_provider_error passed")


async def run_all_tests():
    """Run all tests"""
    print("Running TTS Provider base tests...\n")

    test_tts_result_creation()
    await test_mock_provider_interface()
    test_tts_provider_error()

    print("\n✅ All tests passed successfully!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
