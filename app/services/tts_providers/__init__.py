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
from app.services.tts_providers.edge_tts_provider import EdgeTTSProvider

__all__ = [
    "TTSProvider",
    "TTSProviderError",
    "TTSResult",
    "EdgeTTSProvider",
]
