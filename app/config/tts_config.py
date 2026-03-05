"""
TTS 配置
"""
import os


class TTSConfig:
    """TTS 引擎配置"""

    def __init__(self):
        # 引擎配置
        self.primary_provider: str = os.getenv("TTS_PRIMARY_PROVIDER", "edge-tts")
        self.fallback_providers: list[str] = os.getenv("TTS_FALLBACK_PROVIDERS", "local").split(",")

        # 重试配置
        self.max_retries: int = int(os.getenv("TTS_MAX_RETRIES", "2"))
        self.retry_delay: float = float(os.getenv("TTS_RETRY_DELAY", "0.5"))

        # 故障切换
        self.failure_threshold: int = int(os.getenv("TTS_FAILURE_THRESHOLD", "5"))
        self.cooldown_seconds: int = int(os.getenv("TTS_COOLDOWN_SECONDS", "300"))

        # 缓存配置
        self.enable_cache: bool = os.getenv("TTS_ENABLE_CACHE", "true").lower() == "true"
        self.cache_ttl: int = int(os.getenv("TTS_CACHE_TTL", "86400"))
