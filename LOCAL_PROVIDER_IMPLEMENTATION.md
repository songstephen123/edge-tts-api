# Task 5 Implementation: Local TTS Provider (Offline Fallback)

## Summary

This task implements a local TTS provider using `pyttsx3` as an offline fallback option. The provider will be used when all other providers fail, ensuring the service always has a fallback option.

## Files Created

### 1. `/Users/songstephen/edge-tts-skill/app/services/tts_providers/local_provider.py`

**Key Features:**
- Lazy initialization of pyttsx3 driver
- Thread-safe audio generation using `run_in_executor`
- Proper cleanup of temporary WAV files
- WAV file header validation (`audio_data[:4] == b"RIFF"`)
- Voice caching for performance
- Language detection from voice IDs
- Comprehensive error handling with `TTSProviderError`
- Support for rate and volume parameters (pitch not supported by pyttsx3)

**Properties:**
- `is_free`: True (completely free, works offline)
- `priority`: 3 (lowest priority, as a fallback)

## Files Modified

### 2. `/Users/songstephen/edge-tts-skill/app/services/tts_providers/__init__.py`
- Added `LocalTTSProvider` to imports and `__all__` list

### 3. `/Users/songstephen/edge-tts-skill/app/routes/tts.py`
- Added import for `LocalTTSProvider`
- Registered `LocalTTSProvider()` with `tts_manager`

### 4. `/Users/songstephen/edge-tts-skill/Dockerfile`
- Added espeak dependencies:
  - `espeak`
  - `espeak-data`
  - `libespeak1`
  - `libespeak-dev`

### 5. `/Users/songstephen/edge-tts-skill/requirements.txt`
- Added `pyttsx3==2.90`

## Tests

### 6. `/Users/songstephen/edge-tts-skill/tests/services/test_local_provider.py`
Comprehensive test suite including:
- Property tests (is_free, priority, name)
- Driver initialization tests
- Text-to-speech generation tests
- Parameter handling tests (rate, volume)
- Empty text error handling
- Voice retrieval tests
- Voice caching tests
- Language extraction tests
- Temporary file cleanup verification

### 7. `/Users/songstephen/edge-tts-skill/tests/services/test_local_provider_basic.py`
Basic test suite that works without full dependency installation

## Implementation Details

### Key Design Decisions:

1. **Lazy Initialization**: The pyttsx3 driver is initialized only when first needed (`_get_driver()` method)

2. **Thread Safety**: Audio generation runs in a thread pool executor to avoid blocking the event loop

3. **WAV Format Output**: The provider generates WAV files which are validated using the RIFF header check

4. **Chinese Voice Detection**: The provider attempts to find and use Chinese voices when available

5. **Error Handling**: All exceptions are caught and wrapped in `TTSProviderError` for consistent error handling

6. **Resource Cleanup**: Temporary files are always cleaned up using try-finally blocks

### Provider Priority:

```
1. EdgeTTSProvider (priority=1) - Free, online, high quality
2. LocalTTSProvider (priority=3) - Free, offline, fallback
```

## Usage Example

```python
from app.services.tts_providers.local_provider import LocalTTSProvider

provider = LocalTTSProvider()

# Generate speech
result = await provider.text_to_speech(
    text="你好，这是一个测试",
    voice="default",
    rate="+0%",
    volume="+0%"
)

# Result contains:
# - audio_data: bytes (WAV format)
# - format: "wav"
# - provider: "local"
# - cached: False
```

## Dependencies

### Python:
- `pyttsx3==2.90`

### System (for Docker/Linux):
- `espeak`
- `espeak-data`
- `libespeak1`
- `libespeak-dev`

### System (for macOS):
- `pyobjc` (for Foundation module - nsss driver)
- Or `espeak` (for espeak driver)

## Testing Status

The implementation compiles successfully and passes basic tests:
- ✓ Properties test passed (is_free=True, priority=3)
- ✓ Language extraction test passed
- ✓ Empty text error handling test passed

Note: Full integration tests require espeak/pyobjc dependencies to be installed, which may not be available in all development environments.

## Next Steps

To fully test the implementation:

1. Install system dependencies:
   ```bash
   # On macOS
   brew install espeak

   # Or install pyobjc for macOS native driver
   pip install pyobjc
   ```

2. Run the full test suite:
   ```bash
   pytest tests/services/test_local_provider.py -v
   ```

3. Test the fallback mechanism:
   ```bash
   # Start the server
   uvicorn app.main:app --reload

   # Test TTS with offline fallback
   curl -X POST http://localhost:8000/tts \
     -H "Content-Type: application/json" \
     -d '{"text": "测试本地TTS", "voice": "default"}'
   ```

## Code Quality

- Follows existing code patterns in the codebase
- Comprehensive error handling
- Detailed logging for debugging
- Type hints for better IDE support
- Docstrings for all public methods
- Clean separation of concerns
