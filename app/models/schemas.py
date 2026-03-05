"""
Pydantic 模型定义 - 请求和响应的数据模型
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class TTSRequest(BaseModel):
    """TTS 请求模型"""
    text: str = Field(..., min_length=1, max_length=5000, description="要转换的文本")
    voice: Optional[str] = Field(None, description="音色 ID 或简称")
    rate: Optional[str] = Field("+0%", description="语速，例如: +10%, -20%")
    pitch: Optional[str] = Field("+0Hz", description="音调，例如: +10Hz, -5Hz")
    volume: Optional[str] = Field("+0%", description="音量，例如: +10%, -50%")
    format: Optional[str] = Field("mp3", description="输出格式: mp3 或 opus")

    @field_validator("voice")
    @classmethod
    def resolve_voice_alias(cls, v):
        """解析音色简称"""
        if v is None:
            return None

        # 从配置导入
        from app.config import settings

        # 检查是否是简称
        if v in settings.CHINESE_VOICES:
            return settings.CHINESE_VOICES[v]
        if v in settings.ENGLISH_VOICES:
            return settings.ENGLISH_VOICES[v]

        return v

    @field_validator("rate")
    @classmethod
    def validate_rate(cls, v):
        """验证语速参数格式"""
        if not v.endswith("%"):
            raise ValueError("rate 必须以 % 结尾，例如: +10%, -20%")
        return v

    @field_validator("volume")
    @classmethod
    def validate_volume(cls, v):
        """验证音量参数格式"""
        if not v.endswith("%"):
            raise ValueError("volume 必须以 % 结尾，例如: +10%, -50%")
        return v


class TTSResponse(BaseModel):
    """TTS 响应模型"""
    success: bool
    message: Optional[str] = None
    voice_used: Optional[str] = None
    text_length: Optional[int] = None


class VoiceInfo(BaseModel):
    """音色信息模型"""
    name: str
    id: str
    locale: str
    locale_name: str
    gender: str
    description: Optional[str] = None


class VoicesResponse(BaseModel):
    """音色列表响应"""
    voices: list[VoiceInfo]
    total: int


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str
    edge_tts_available: bool
