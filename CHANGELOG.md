# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Multi-provider TTS architecture with Provider pattern
- TTS Manager core dispatcher for automatic provider selection
- Edge TTS Provider (free primary engine)
- Local TTS Provider (offline fallback)
- TTS configuration system with environment variable support
- Performance metrics collection and monitoring
- Automatic failure degradation and cooldown mechanism
- Docker deployment support with docker-compose
- Comprehensive test suite for all TTS components
- New API endpoints: /tts/providers, /tts/stats, /tts/metrics
- Provider parameter for forcing specific TTS engine
- Response headers: X-TTS-Provider, X-TTS-Cached

### Changed
- TTS routes now use TTSManager for provider abstraction
- Added provider parameter support to all TTS endpoints
- Response headers include provider and caching information
- Enhanced error handling with automatic fallback

### Fixed
- Edge TTS 403 error handling (automatic degradation to local provider)
- Fixed asyncio.BytesIO import (changed to io.BytesIO)
- Improved failure tracking and cooldown logic

## [2.0.0] - 2026-03-05

### Added
- Initial release of multi-provider TTS architecture
- Support for Edge TTS and Local TTS engines
- Automatic failover and cooldown mechanisms
- Docker deployment support
- Comprehensive documentation and examples

### Features
- Provider pattern for extensible TTS backends
- Health monitoring and failure statistics
- Performance metrics (latency, cache hit rate, provider distribution)
- Environment-based configuration
- Python client and integration examples (Feishu, DingTalk)
