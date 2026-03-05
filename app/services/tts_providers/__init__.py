"""
TTS Providers package

This package contains implementations of various TTS providers
that share a common interface defined in base.py.
"""
from app.services.tts_providers.base import (
    TTSProvider,
    TTSProviderError,
    TTSResult
)

__all__ = [
    "TTSProvider",
    "TTSProviderError",
    "TTSResult"
]
