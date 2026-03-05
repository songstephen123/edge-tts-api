"""
Tests for TTS Manager - the core dispatcher
"""
import pytest
import asyncio
from typing import List
from unittest.mock import AsyncMock

from app.services.tts_manager import TTSManager, TTSAllFailedError
from app.services.tts_providers.base import (
    TTSProvider,
    TTSResult,
    TTSProviderError
)
from app.config.tts_config import TTSConfig


class MockSuccessProvider(TTSProvider):
    """Mock provider that always succeeds"""

    def __init__(self, name: str = "MockSuccessProvider", priority: int = 100):
        self._name = name
        self._priority = priority
        self.call_count = 0
        self.last_params = None

    @property
    def is_free(self) -> bool:
        return True

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def name(self) -> str:
        return self._name

    async def text_to_speech(
        self,
        text: str,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> TTSResult:
        self.call_count += 1
        self.last_params = {
            "text": text,
            "voice": voice,
            "rate": rate,
            "pitch": pitch,
            "volume": volume
        }
        return TTSResult(
            audio_data=b"mock_audio_data",
            format="mp3",
            provider=self._name,
            cached=False
        )

    async def get_available_voices(self) -> List[dict]:
        return [{"id": "mock-voice-1", "name": "Mock Voice 1"}]


class MockFailureProvider(TTSProvider):
    """Mock provider that always fails"""

    def __init__(
        self,
        name: str = "MockFailureProvider",
        priority: int = 50,
        fail_count: int = 0
    ):
        self._name = name
        self._priority = priority
        self.call_count = 0
        self.fail_count = fail_count  # Fail this many times before succeeding

    @property
    def is_free(self) -> bool:
        return True

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def name(self) -> str:
        return self._name

    async def text_to_speech(
        self,
        text: str,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> TTSResult:
        self.call_count += 1
        # If fail_count is -1, always fail
        # Otherwise fail until call_count exceeds fail_count
        if self.fail_count == -1 or (self.fail_count > 0 and self.call_count <= self.fail_count):
            raise TTSProviderError(f"{self._name} failed")
        return TTSResult(
            audio_data=b"mock_audio_data",
            format="mp3",
            provider=self._name,
            cached=False
        )

    async def get_available_voices(self) -> List[dict]:
        return [{"id": "mock-voice-1", "name": "Mock Voice 1"}]


def test_tts_manager_initialization():
    """Test TTSManager initialization"""
    manager = TTSManager()

    assert manager.get_providers() == []
    assert manager.get_stats()["total_providers"] == 0
    assert manager.get_stats()["available_providers"] == 0


def test_tts_manager_with_config():
    """Test TTSManager initialization with config"""
    config = TTSConfig(failure_threshold=10, cooldown_seconds=600)
    manager = TTSManager(config=config)

    assert manager._failure_threshold == 10
    assert manager._cooldown_seconds == 600


def test_tts_manager_without_config():
    """Test TTSManager initialization without config uses defaults"""
    manager = TTSManager()

    assert manager._failure_threshold == 5
    assert manager._cooldown_seconds == 300


def test_register_providers():
    """Test provider registration and priority sorting"""
    manager = TTSManager()

    # Register providers with different priorities
    low_priority = MockSuccessProvider("LowPriority", priority=10)
    high_priority = MockSuccessProvider("HighPriority", priority=100)
    medium_priority = MockSuccessProvider("MediumPriority", priority=50)

    manager.register_provider(low_priority)
    manager.register_provider(high_priority)
    manager.register_provider(medium_priority)

    providers = manager.get_providers()

    # Check that all providers are registered
    assert len(providers) == 3

    # Check that providers are sorted by priority (descending)
    assert providers[0].name == "HighPriority"
    assert providers[1].name == "MediumPriority"
    assert providers[2].name == "LowPriority"


def test_register_duplicate_provider():
    """Test that duplicate providers are not registered twice"""
    manager = TTSManager()
    provider = MockSuccessProvider()

    manager.register_provider(provider)
    manager.register_provider(provider)

    providers = manager.get_providers()
    assert len(providers) == 1


@pytest.mark.asyncio
async def test_text_to_speech_success():
    """Test successful text to speech conversion"""
    manager = TTSManager()
    provider = MockSuccessProvider()

    manager.register_provider(provider)

    result = await manager.text_to_speech(
        text="Hello, world!",
        voice="mock-voice-1"
    )

    assert result.audio_data == b"mock_audio_data"
    assert result.format == "mp3"
    assert result.provider == "MockSuccessProvider"
    assert result.cached is False

    # Check provider was called once
    assert provider.call_count == 1
    assert provider.last_params["text"] == "Hello, world!"


@pytest.mark.asyncio
async def test_text_to_speech_with_parameters():
    """Test text to speech with rate, pitch, and volume parameters"""
    manager = TTSManager()
    provider = MockSuccessProvider()

    manager.register_provider(provider)

    result = await manager.text_to_speech(
        text="Test",
        voice="mock-voice-1",
        rate="+10%",
        pitch="+5Hz",
        volume="+10%"
    )

    assert result.audio_data == b"mock_audio_data"

    # Check provider was called with correct parameters
    assert provider.last_params["rate"] == "+10%"
    assert provider.last_params["pitch"] == "+5Hz"
    assert provider.last_params["volume"] == "+10%"


@pytest.mark.asyncio
async def test_fallback_on_failure():
    """Test automatic fallback when a provider fails"""
    manager = TTSManager()

    failing_provider = MockFailureProvider("FailingProvider", priority=50, fail_count=-1)
    fallback_provider = MockSuccessProvider("FallbackProvider", priority=10)

    manager.register_provider(failing_provider)
    manager.register_provider(fallback_provider)

    result = await manager.text_to_speech(
        text="Hello, world!",
        voice="mock-voice-1"
    )

    # Should have used the fallback provider
    assert result.provider == "FallbackProvider"
    assert failing_provider.call_count == 1
    assert fallback_provider.call_count == 1


@pytest.mark.asyncio
async def test_all_providers_fail():
    """Test error when all providers fail"""
    manager = TTSManager()

    failing_provider1 = MockFailureProvider("FailingProvider1", priority=100, fail_count=-1)
    failing_provider2 = MockFailureProvider("FailingProvider2", priority=50, fail_count=-1)

    manager.register_provider(failing_provider1)
    manager.register_provider(failing_provider2)

    with pytest.raises(TTSAllFailedError) as exc_info:
        await manager.text_to_speech(
            text="Hello, world!",
            voice="mock-voice-1"
        )

    assert "所有 TTS 提供者均失败" in str(exc_info.value)


@pytest.mark.asyncio
async def test_no_providers_registered():
    """Test error when no providers are registered"""
    manager = TTSManager()

    with pytest.raises(TTSAllFailedError) as exc_info:
        await manager.text_to_speech(
            text="Hello, world!",
            voice="mock-voice-1"
        )

    assert "没有可用的 TTS 提供者" in str(exc_info.value)


@pytest.mark.asyncio
async def test_force_provider():
    """Test forcing a specific provider"""
    manager = TTSManager()

    provider1 = MockSuccessProvider("Provider1", priority=100)
    provider2 = MockSuccessProvider("Provider2", priority=50)

    manager.register_provider(provider1)
    manager.register_provider(provider2)

    # Force using Provider2 (lower priority)
    result = await manager.text_to_speech(
        text="Hello, world!",
        voice="mock-voice-1",
        force_provider="Provider2"
    )

    assert result.provider == "Provider2"
    assert provider1.call_count == 0
    assert provider2.call_count == 1


@pytest.mark.asyncio
async def test_force_provider_not_found():
    """Test error when forcing a non-existent provider"""
    manager = TTSManager()
    provider = MockSuccessProvider()

    manager.register_provider(provider)

    with pytest.raises(TTSAllFailedError) as exc_info:
        await manager.text_to_speech(
            text="Hello, world!",
            voice="mock-voice-1",
            force_provider="NonExistentProvider"
        )

    assert "指定的提供者 NonExistentProvider 不可用或未注册" in str(exc_info.value)


@pytest.mark.asyncio
async def test_failure_tracking_and_cooldown():
    """Test failure counting and cooldown mechanism"""
    manager = TTSManager()

    # Set a low threshold for testing
    manager._failure_threshold = 3

    provider = MockFailureProvider("TestProvider", priority=100, fail_count=10)
    manager.register_provider(provider)

    # Fail until cooldown is triggered
    for _ in range(3):
        with pytest.raises(TTSAllFailedError):
            await manager.text_to_speech(
                text="Test",
                voice="mock-voice-1"
            )

    # Provider should now be in cooldown
    assert not manager._is_provider_available(provider)

    # Stats should show provider as unavailable
    stats = manager.get_stats()
    provider_stats = next(p for p in stats["providers"] if p["name"] == "TestProvider")
    assert provider_stats["failure_count"] == 3
    assert provider_stats["available"] is False
    assert provider_stats["disabled_until"] is not None


@pytest.mark.asyncio
async def test_success_resets_failure_count():
    """Test that successful calls reset failure count"""
    manager = TTSManager()

    manager._failure_threshold = 5

    # Provider that fails twice, then succeeds
    provider = MockFailureProvider("TestProvider", priority=100, fail_count=2)
    manager.register_provider(provider)

    # Fail twice
    for _ in range(2):
        with pytest.raises(TTSAllFailedError):
            await manager.text_to_speech(
                text="Test",
                voice="mock-voice-1"
            )

    assert manager._failure_counts["TestProvider"] == 2

    # Third call should succeed
    result = await manager.text_to_speech(
        text="Test",
        voice="mock-voice-1"
    )

    assert result.provider == "TestProvider"
    assert manager._failure_counts["TestProvider"] == 0


def test_get_stats():
    """Test getting statistics"""
    manager = TTSManager()

    provider1 = MockSuccessProvider("Provider1", priority=100)
    provider2 = MockSuccessProvider("Provider2", priority=50)

    manager.register_provider(provider1)
    manager.register_provider(provider2)

    stats = manager.get_stats()

    assert stats["total_providers"] == 2
    assert stats["available_providers"] == 2

    # Check provider stats
    provider1_stats = next(p for p in stats["providers"] if p["name"] == "Provider1")
    assert provider1_stats["priority"] == 100
    assert provider1_stats["is_free"] is True
    assert provider1_stats["failure_count"] == 0
    assert provider1_stats["available"] is True

    provider2_stats = next(p for p in stats["providers"] if p["name"] == "Provider2")
    assert provider2_stats["priority"] == 50


@pytest.mark.asyncio
async def test_cooldown_expiration():
    """Test that providers become available after cooldown expires"""
    manager = TTSManager()

    # Set very short cooldown for testing
    manager._failure_threshold = 2
    manager._cooldown_seconds = 0.1  # 100ms

    provider = MockFailureProvider("TestProvider", priority=100, fail_count=10)
    manager.register_provider(provider)

    # Trigger cooldown
    for _ in range(2):
        with pytest.raises(TTSAllFailedError):
            await manager.text_to_speech(
                text="Test",
                voice="mock-voice-1"
            )

    assert not manager._is_provider_available(provider)

    # Wait for cooldown to expire
    await asyncio.sleep(0.15)

    # Provider should be available again
    assert manager._is_provider_available(provider)
    assert manager._failure_counts["TestProvider"] == 0


@pytest.mark.asyncio
async def test_all_providers_in_cooldown():
    """Test error when all providers are in cooldown"""
    manager = TTSManager()

    manager._failure_threshold = 1

    provider1 = MockFailureProvider("Provider1", priority=100, fail_count=10)
    provider2 = MockFailureProvider("Provider2", priority=50, fail_count=10)

    manager.register_provider(provider1)
    manager.register_provider(provider2)

    # Trigger cooldown for both providers
    with pytest.raises(TTSAllFailedError):
        await manager.text_to_speech(
            text="Test",
            voice="mock-voice-1",
            force_provider="Provider1"
        )

    with pytest.raises(TTSAllFailedError):
        await manager.text_to_speech(
            text="Test",
            voice="mock-voice-1",
            force_provider="Provider2"
        )

    # Now all providers should be in cooldown
    with pytest.raises(TTSAllFailedError) as exc_info:
        await manager.text_to_speech(
            text="Test",
            voice="mock-voice-1"
        )

    assert "所有提供者均处于冷却状态" in str(exc_info.value)
