"""
配置管理 - 从环境变量加载配置
"""
import os
from typing import List
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 导入 TTS 配置
from app.config.tts_config import TTSConfig


class Settings:
    """应用配置"""

    # 服务配置
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8000"))
    SERVICE_HOST: str = os.getenv("SERVICE_HOST", "0.0.0.0")

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # CORS 配置
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", "*"
    ).split(",") if os.getenv("CORS_ORIGINS") != "*" else ["*"]

    # 默认 TTS 设置
    DEFAULT_VOICE: str = os.getenv("DEFAULT_VOICE", "zh-CN-XiaoxiaoNeural")
    DEFAULT_RATE: str = os.getenv("DEFAULT_RATE", "+0%")
    DEFAULT_PITCH: str = os.getenv("DEFAULT_PITCH", "+0Hz")
    DEFAULT_VOLUME: str = os.getenv("DEFAULT_VOLUME", "+0%")

    # 缓存配置
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))

    # 常用中文音色
    CHINESE_VOICES = {
        "xiaoxiao": "zh-CN-XiaoxiaoNeural",  # 女 - 温柔
        "xiaoyi": "zh-CN-XiaoyiNeural",      # 女 - 亲和
        "xiaohan": "zh-CN-XiaohanNeural",    # 女 - 清脆
        "xiaomeng": "zh-CN-XiaomengNeural",  # 女 - 童声
        "yunyang": "zh-CN-YunyangNeural",    # 男 - 成熟
        "yunjian": "zh-CN-YunjianNeural",    # 男 - 沉稳
    }

    # 常用英文音色
    ENGLISH_VOICES = {
        "aria": "en-US-AriaNeural",          # 女
        "guy": "en-US-GuyNeural",            # 男
        "jenny": "en-US-JennyNeural",        # 女
    }


settings = Settings()
tts_config = TTSConfig()
