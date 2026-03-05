"""
Base classes and interfaces for TTS providers

This module defines the abstract interface that all TTS providers must implement,
allowing for a multi-provider architecture with automatic fallback.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TTSResult:
    """Result from TTS generation

    Attributes:
        audio_data: Generated audio data as bytes
        format: Audio format (e.g., "mp3", "wav")
        provider: Name of the provider that generated the audio
        cached: Whether the result was retrieved from cache
    """
    audio_data: bytes
    format: str
    provider: str
    cached: bool


class TTSProviderError(Exception):
    """Exception raised when TTS provider fails

    This exception is raised when a TTS provider encounters an error
    during audio generation or voice retrieval.
    """
    pass


class TTSProvider(ABC):
    """Abstract base class for TTS providers

    All TTS providers must inherit from this class and implement
    the required abstract methods.
    """

    @abstractmethod
    async def text_to_speech(
        self,
        text: str,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> TTSResult:
        """Convert text to speech

        Args:
            text: The text to convert to speech
            voice: Voice ID to use for synthesis
            rate: Speaking rate adjustment (default: "+0%")
            pitch: Pitch adjustment (default: "+0Hz")
            volume: Volume adjustment (default: "+0%")

        Returns:
            TTSResult containing the audio data and metadata

        Raises:
            TTSProviderError: If TTS generation fails
        """
        pass

    @abstractmethod
    async def get_available_voices(self) -> List[dict]:
        """Get list of available voices

        Returns:
            List of voice dictionaries containing voice metadata.
            Each voice dict should at minimum contain an 'id' field.

        Raises:
            TTSProviderError: If voice retrieval fails
        """
        pass

    @property
    @abstractmethod
    def is_free(self) -> bool:
        """Whether this provider is free to use

        Returns:
            True if the provider is free, False otherwise
        """
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """Provider priority for fallback selection

        Higher priority providers are tried first.
        Free providers should generally have higher priority
        than paid ones.

        Returns:
            Integer priority value (higher = tried first)
        """
        pass

    @property
    def name(self) -> str:
        """Get provider name

        Returns:
            The class name of the provider
        """
        return self.__class__.__name__
