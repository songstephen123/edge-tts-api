"""
Simple test runner for TTS Manager tests
"""
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.tts_manager import TTSManager, TTSAllFailedError
from app.services.tts_providers.base import (
    TTSProvider,
    TTSResult,
    TTSProviderError
)
from typing import List


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
        self.fail_count = fail_count

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


async def run_tests():
    """Run all tests"""
    tests_passed = 0
    tests_failed = 0

    print("Running TTS Manager Tests...")
    print("=" * 60)

    # Test 1: Initialization
    print("\n[Test 1] Testing TTSManager initialization...")
    try:
        manager = TTSManager()
        assert manager.get_providers() == []
        assert manager.get_stats()["total_providers"] == 0
        print("  ✓ PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        tests_failed += 1

    # Test 2: Register providers and priority sorting
    print("\n[Test 2] Testing provider registration and priority sorting...")
    try:
        manager = TTSManager()
        low_priority = MockSuccessProvider("LowPriority", priority=10)
        high_priority = MockSuccessProvider("HighPriority", priority=100)
        medium_priority = MockSuccessProvider("MediumPriority", priority=50)

        manager.register_provider(low_priority)
        manager.register_provider(high_priority)
        manager.register_provider(medium_priority)

        providers = manager.get_providers()
        assert len(providers) == 3
        assert providers[0].name == "HighPriority"
        assert providers[1].name == "MediumPriority"
        assert providers[2].name == "LowPriority"
        print("  ✓ PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        tests_failed += 1

    # Test 3: Duplicate provider registration
    print("\n[Test 3] Testing duplicate provider registration...")
    try:
        manager = TTSManager()
        provider = MockSuccessProvider()
        manager.register_provider(provider)
        manager.register_provider(provider)

        providers = manager.get_providers()
        assert len(providers) == 1
        print("  ✓ PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        tests_failed += 1

    # Test 4: Text to speech success
    print("\n[Test 4] Testing text to speech success...")
    try:
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
        assert provider.call_count == 1
        print("  ✓ PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        tests_failed += 1

    # Test 5: Text to speech with parameters
    print("\n[Test 5] Testing text to speech with parameters...")
    try:
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
        assert provider.last_params["rate"] == "+10%"
        assert provider.last_params["pitch"] == "+5Hz"
        assert provider.last_params["volume"] == "+10%"
        print("  ✓ PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        tests_failed += 1

    # Test 6: Fallback on failure
    print("\n[Test 6] Testing fallback on provider failure...")
    try:
        manager = TTSManager()
        failing_provider = MockFailureProvider("FailingProvider", priority=50, fail_count=-1)
        fallback_provider = MockSuccessProvider("FallbackProvider", priority=10)

        manager.register_provider(failing_provider)
        manager.register_provider(fallback_provider)

        result = await manager.text_to_speech(
            text="Hello, world!",
            voice="mock-voice-1"
        )

        assert result.provider == "FallbackProvider"
        assert failing_provider.call_count == 1
        assert fallback_provider.call_count == 1
        print("  ✓ PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        tests_failed += 1

    # Test 7: All providers fail
    print("\n[Test 7] Testing all providers fail...")
    try:
        manager = TTSManager()
        failing_provider1 = MockFailureProvider("FailingProvider1", priority=100, fail_count=-1)
        failing_provider2 = MockFailureProvider("FailingProvider2", priority=50, fail_count=-1)

        manager.register_provider(failing_provider1)
        manager.register_provider(failing_provider2)

        error_raised = False
        try:
            await manager.text_to_speech(
                text="Hello, world!",
                voice="mock-voice-1"
            )
        except TTSAllFailedError:
            error_raised = True

        assert error_raised
        print("  ✓ PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        tests_failed += 1

    # Test 8: No providers registered
    print("\n[Test 8] Testing no providers registered...")
    try:
        manager = TTSManager()
        error_raised = False
        try:
            await manager.text_to_speech(
                text="Hello, world!",
                voice="mock-voice-1"
            )
        except TTSAllFailedError:
            error_raised = True

        assert error_raised
        print("  ✓ PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        tests_failed += 1

    # Test 9: Force provider
    print("\n[Test 9] Testing force provider...")
    try:
        manager = TTSManager()
        provider1 = MockSuccessProvider("Provider1", priority=100)
        provider2 = MockSuccessProvider("Provider2", priority=50)

        manager.register_provider(provider1)
        manager.register_provider(provider2)

        result = await manager.text_to_speech(
            text="Hello, world!",
            voice="mock-voice-1",
            force_provider="Provider2"
        )

        assert result.provider == "Provider2"
        assert provider1.call_count == 0
        assert provider2.call_count == 1
        print("  ✓ PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        tests_failed += 1

    # Test 10: Force provider not found
    print("\n[Test 10] Testing force provider not found...")
    try:
        manager = TTSManager()
        provider = MockSuccessProvider()
        manager.register_provider(provider)

        error_raised = False
        try:
            await manager.text_to_speech(
                text="Hello, world!",
                voice="mock-voice-1",
                force_provider="NonExistentProvider"
            )
        except TTSAllFailedError:
            error_raised = True

        assert error_raised
        print("  ✓ PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        tests_failed += 1

    # Test 11: Failure tracking and cooldown
    print("\n[Test 11] Testing failure tracking and cooldown...")
    try:
        manager = TTSManager()
        manager._failure_threshold = 3

        provider = MockFailureProvider("TestProvider", priority=100, fail_count=10)
        manager.register_provider(provider)

        for _ in range(3):
            try:
                await manager.text_to_speech(
                    text="Test",
                    voice="mock-voice-1"
                )
            except TTSAllFailedError:
                pass

        assert not manager._is_provider_available(provider)

        stats = manager.get_stats()
        provider_stats = next(p for p in stats["providers"] if p["name"] == "TestProvider")
        assert provider_stats["failure_count"] == 3
        assert provider_stats["available"] is False
        assert provider_stats["disabled_until"] is not None
        print("  ✓ PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        tests_failed += 1

    # Test 12: Success resets failure count
    print("\n[Test 12] Testing success resets failure count...")
    try:
        manager = TTSManager()
        manager._failure_threshold = 5

        provider = MockFailureProvider("TestProvider", priority=100, fail_count=2)
        manager.register_provider(provider)

        for _ in range(2):
            try:
                await manager.text_to_speech(
                    text="Test",
                    voice="mock-voice-1"
                )
            except TTSAllFailedError:
                pass

        assert manager._failure_counts["TestProvider"] == 2

        result = await manager.text_to_speech(
            text="Test",
            voice="mock-voice-1"
        )

        assert result.provider == "TestProvider"
        assert manager._failure_counts["TestProvider"] == 0
        print("  ✓ PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        tests_failed += 1

    # Test 13: Get stats
    print("\n[Test 13] Testing get_stats...")
    try:
        manager = TTSManager()
        provider1 = MockSuccessProvider("Provider1", priority=100)
        provider2 = MockSuccessProvider("Provider2", priority=50)

        manager.register_provider(provider1)
        manager.register_provider(provider2)

        stats = manager.get_stats()

        assert stats["total_providers"] == 2
        assert stats["available_providers"] == 2

        provider1_stats = next(p for p in stats["providers"] if p["name"] == "Provider1")
        assert provider1_stats["priority"] == 100
        assert provider1_stats["is_free"] is True

        print("  ✓ PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        tests_failed += 1

    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"Total Tests: {tests_passed + tests_failed}")
    print("=" * 60)

    return tests_failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
