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
from app.services.tts_providers.local_provider import LocalTTSProvider

__all__ = [
    "TTSProvider",
    "TTSProviderError",
    "TTSResult",
    "EdgeTTSProvider",
    "LocalTTSProvider",
]
