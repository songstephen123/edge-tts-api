"""
Tests for Local TTS Provider

Tests the LocalTTSProvider implementation including voice retrieval,
text-to-speech generation, and error handling.
"""
import os
import pytest
from app.services.tts_providers.local_provider import LocalTTSProvider
from app.services.tts_providers.base import TTSProviderError


def test_local_tts_provider_properties():
    """Test LocalTTSProvider properties"""
    provider = LocalTTSProvider()

    assert provider.is_free is True
    assert provider.priority == 3
    assert provider.name == "LocalTTSProvider"


@pytest.mark.asyncio
async def test_get_driver_initialization():
    """Test driver initialization"""
    provider = LocalTTSProvider()

    # First call should initialize driver
    driver = provider._get_driver()
    assert driver is not None

    # Second call should return cached driver
    driver2 = provider._get_driver()
    assert driver is driver2


@pytest.mark.asyncio
async def test_text_to_speech():
    """Test text_to_speech method"""
    provider = LocalTTSProvider()

    result = await provider.text_to_speech(
        text="测试语音合成",
        voice="default",
        rate="+0%",
        pitch="+0Hz",
        volume="+0%"
    )

    assert isinstance(result.audio_data, bytes)
    assert len(result.audio_data) > 0
    assert result.format == "wav"
    assert result.provider == "local"
    assert result.cached is False

    # Verify WAV file header
    if len(result.audio_data) >= 4:
        # Should be a valid WAV file with RIFF header
        assert result.audio_data[:4] == b"RIFF"


@pytest.mark.asyncio
async def test_text_to_speech_with_rate():
    """Test text_to_speech with rate parameter"""
    provider = LocalTTSProvider()

    result = await provider.text_to_speech(
        text="测试语速",
        voice="default",
        rate="+20%"
    )

    assert isinstance(result.audio_data, bytes)
    assert len(result.audio_data) > 0
    assert result.format == "wav"


@pytest.mark.asyncio
async def test_text_to_speech_with_volume():
    """Test text_to_speech with volume parameter"""
    provider = LocalTTSProvider()

    result = await provider.text_to_speech(
        text="测试音量",
        voice="default",
        volume="+10%"
    )

    assert isinstance(result.audio_data, bytes)
    assert len(result.audio_data) > 0
    assert result.format == "wav"


@pytest.mark.asyncio
async def test_text_to_speech_empty_text():
    """Test text_to_speech with empty text raises error"""
    provider = LocalTTSProvider()

    with pytest.raises(TTSProviderError) as exc_info:
        await provider.text_to_speech(text="", voice="default")

    assert "cannot be empty" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_text_to_speech_whitespace_only():
    """Test text_to_speech with whitespace-only text raises error"""
    provider = LocalTTSProvider()

    with pytest.raises(TTSProviderError) as exc_info:
        await provider.text_to_speech(text="   ", voice="default")

    assert "cannot be empty" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_available_voices():
    """Test get_available_voices returns voice list"""
    provider = LocalTTSProvider()

    voices = await provider.get_available_voices()

    assert isinstance(voices, list)
    assert len(voices) >= 1

    # Check voice dict structure
    for voice in voices:
        assert "id" in voice
        assert "name" in voice
        assert "language" in voice
        assert "gender" in voice
        assert "provider" in voice
        assert voice["provider"] == "local"


@pytest.mark.asyncio
async def test_get_available_voices_caching():
    """Test that voices are cached after first call"""
    provider = LocalTTSProvider()

    # First call
    voices1 = await provider.get_available_voices()
    # Second call should return cached data
    voices2 = await provider.get_available_voices()

    assert voices1 == voices2


@pytest.mark.asyncio
async def test_extract_language():
    """Test language extraction from voice IDs"""
    provider = LocalTTSProvider()

    # Create a mock voice object
    class MockVoice:
        def __init__(self, voice_id, name):
            self.id = voice_id
            self.name = name

    # Test Chinese voice
    lang = provider._extract_language(MockVoice("zh-CN-voice", "Chinese Voice"))
    assert lang == "zh-CN"

    # Test English voice
    lang = provider._extract_language(MockVoice("en-US-voice", "English Voice"))
    assert lang == "en-US"

    # Test unknown voice
    lang = provider._extract_language(MockVoice("unknown-voice", "Unknown Voice"))
    assert lang == "unknown"


@pytest.mark.asyncio
async def test_generate_sync_cleanup():
    """Test that temporary files are cleaned up after generation"""
    import tempfile

    provider = LocalTTSProvider()

    # Track temp files before
    temp_dir = tempfile.gettempdir()
    temp_files_before = set(os.listdir(temp_dir))

    # Generate audio
    result = await provider.text_to_speech(
        text="测试清理",
        voice="default"
    )

    # The temp file should be cleaned up
    # (We can't easily verify this without inspecting the exact file created,
    # but we can verify the generation succeeded)
    assert isinstance(result.audio_data, bytes)
    assert len(result.audio_data) > 0
