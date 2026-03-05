"""
Tests for Edge TTS Provider

Tests the EdgeTTSProvider implementation including voice mapping,
text-to-speech generation, and error handling.
"""
import pytest
from app.services.tts_providers.edge_tts_provider import EdgeTTSProvider
from app.services.tts_providers.base import TTSProviderError


def test_edge_tts_provider_properties():
    """Test EdgeTTSProvider properties"""
    provider = EdgeTTSProvider()

    assert provider.is_free is True
    assert provider.priority == 1
    assert provider.name == "EdgeTTSProvider"


def test_voice_resolution():
    """Test voice resolution from short names to full IDs"""
    provider = EdgeTTSProvider()

    # Test short name resolution
    assert provider._resolve_voice("xiaoxiao") == "zh-CN-XiaoxiaoNeural"
    assert provider._resolve_voice("yunyang") == "zh-CN-YunyangNeural"
    assert provider._resolve_voice("xiaoyi") == "zh-CN-XiaoyiNeural"
    assert provider._resolve_voice("xiaohan") == "zh-CN-XiaohanNeural"
    assert provider._resolve_voice("xiaomeng") == "zh-CN-XiaomengNeural"

    # Test full ID passthrough
    full_id = "zh-CN-XiaoxiaoNeural"
    assert provider._resolve_voice(full_id) == full_id

    # Test unknown short name returns as-is
    unknown = "unknown-voice"
    assert provider._resolve_voice(unknown) == unknown


@pytest.mark.asyncio
async def test_text_to_speech():
    """Test text_to_speech method with actual edge-tts library"""
    provider = EdgeTTSProvider()

    result = await provider.text_to_speech(
        text="测试语音合成",
        voice="xiaoxiao",
        rate="+0%",
        pitch="+0Hz",
        volume="+0%"
    )

    assert isinstance(result.audio_data, bytes)
    assert len(result.audio_data) > 0
    assert result.format == "mp3"
    assert result.provider == "EdgeTTSProvider"
    assert result.cached is False


@pytest.mark.asyncio
async def test_text_to_speech_with_full_voice_id():
    """Test text_to_speech with full voice ID"""
    provider = EdgeTTSProvider()

    result = await provider.text_to_speech(
        text="Hello world",
        voice="zh-CN-XiaoxiaoNeural"
    )

    assert isinstance(result.audio_data, bytes)
    assert len(result.audio_data) > 0
    assert result.format == "mp3"


@pytest.mark.asyncio
async def test_text_to_speech_with_parameters():
    """Test text_to_speech with rate, pitch, and volume parameters"""
    provider = EdgeTTSProvider()

    result = await provider.text_to_speech(
        text="测试参数",
        voice="xiaoxiao",
        rate="+10%",
        pitch="+5Hz",
        volume="+10%"
    )

    assert isinstance(result.audio_data, bytes)
    assert len(result.audio_data) > 0


@pytest.mark.asyncio
async def test_text_to_speech_empty_text():
    """Test text_to_speech with empty text raises error"""
    provider = EdgeTTSProvider()

    with pytest.raises(TTSProviderError):
        await provider.text_to_speech(text="", voice="xiaoxiao")


@pytest.mark.asyncio
async def test_get_available_voices():
    """Test get_available_voices returns preset voice list"""
    provider = EdgeTTSProvider()

    voices = await provider.get_available_voices()

    assert isinstance(voices, list)
    assert len(voices) >= 5

    # Check for expected voice IDs
    voice_ids = [v["id"] for v in voices]
    assert "zh-CN-XiaoxiaoNeural" in voice_ids
    assert "zh-CN-YunyangNeural" in voice_ids
    assert "zh-CN-XiaoyiNeural" in voice_ids
    assert "zh-CN-XiaohanNeural" in voice_ids
    assert "zh-CN-XiaomengNeural" in voice_ids

    # Check voice dict structure
    for voice in voices:
        assert "id" in voice
        assert "name" in voice
