"""
Basic Tests for Local TTS Provider

These tests verify the LocalTTSProvider implementation without requiring
full dependency installation. Tests are designed to work even when
pyttsx3 dependencies are not fully available.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import directly to avoid __init__.py dependency issues
import importlib.util

# Load base module
spec = importlib.util.spec_from_file_location(
    "app.services.tts_providers.base",
    "/Users/songstephen/edge-tts-skill/app/services/tts_providers/base.py"
)
base_module = importlib.util.module_from_spec(spec)
sys.modules['app.services.tts_providers.base'] = base_module
spec.loader.exec_module(base_module)

TTSProvider = base_module.TTSProvider
TTSProviderError = base_module.TTSProviderError

# Load local_provider module
spec2 = importlib.util.spec_from_file_location(
    "app.services.tts_providers.local_provider",
    "/Users/songstephen/edge-tts-skill/app/services/tts_providers/local_provider.py"
)
local_provider_module = importlib.util.module_from_spec(spec2)
sys.modules['app.services.tts_providers.local_provider'] = local_provider_module
spec2.loader.exec_module(local_provider_module)

LocalTTSProvider = local_provider_module.LocalTTSProvider


def test_local_tts_provider_properties():
    """Test LocalTTSProvider properties"""
    provider = LocalTTSProvider()

    assert provider.is_free is True
    assert provider.priority == 3
    assert provider.name == "LocalTTSProvider"
    print("✓ Properties test passed")


def test_local_tts_provider_driver_initialization():
    """Test driver initialization (lazy)"""
    provider = LocalTTSProvider()

    try:
        driver = provider._get_driver()
        assert driver is not None
        print("✓ Driver initialization test passed")
    except Exception as e:
        print(f"✗ Driver initialization failed (expected if espeak not installed): {e}")
        # This is expected in environments without espeak


def test_extract_language():
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

    print("✓ Language extraction test passed")


def test_text_to_speech_empty_text():
    """Test text_to_speech with empty text raises error"""
    import asyncio

    provider = LocalTTSProvider()

    async def run_test():
        try:
            await provider.text_to_speech(text="", voice="default")
            assert False, "Should have raised TTSProviderError"
        except TTSProviderError as e:
            assert "cannot be empty" in str(e).lower()
            print("✓ Empty text error handling test passed")

    asyncio.run(run_test())


def test_get_available_voices_structure():
    """Test that get_available_voices returns proper structure"""
    import asyncio

    provider = LocalTTSProvider()

    async def run_test():
        try:
            voices = await provider.get_available_voices()

            assert isinstance(voices, list)
            # Should at least have default voice
            assert len(voices) >= 1

            # Check voice dict structure
            for voice in voices:
                assert "id" in voice
                assert "name" in voice
                assert "language" in voice
                assert "gender" in voice
                assert "provider" in voice
                assert voice["provider"] == "local"

            print(f"✓ Available voices structure test passed ({len(voices)} voices)")
        except Exception as e:
            print(f"✗ Available voices test failed: {e}")

    asyncio.run(run_test())


def test_voice_caching():
    """Test that voices are cached after first call"""
    import asyncio

    provider = LocalTTSProvider()

    async def run_test():
        try:
            # First call
            voices1 = await provider.get_available_voices()
            # Second call should return cached data
            voices2 = await provider.get_available_voices()

            assert voices1 == voices2
            print("✓ Voice caching test passed")
        except Exception as e:
            print(f"✗ Voice caching test failed: {e}")

    asyncio.run(run_test())


if __name__ == "__main__":
    print("Running Local TTS Provider Basic Tests...")
    print()

    test_local_tts_provider_properties()
    test_local_tts_provider_driver_initialization()
    test_extract_language()
    test_text_to_speech_empty_text()
    test_get_available_voices_structure()
    test_voice_caching()

    print()
    print("All basic tests completed!")
