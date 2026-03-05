"""
TTS 配置
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class TTSConfig(BaseSettings):
    """TTS 引擎配置"""

    # 引擎配置
    primary_provider: str = "edge-tts"
    fallback_providers: list[str] = ["local"]

    # 重试配置
    max_retries: int = 2
    retry_delay: float = 0.5

    # 故障切换
    failure_threshold: int = 5
    cooldown_seconds: int = 300

    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 86400  # 24 小时

    model_config = SettingsConfigDict(
        env_prefix="TTS_",
        env_file=".env"
    )
