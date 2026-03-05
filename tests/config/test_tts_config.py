import pytest
from app.config.tts_config import TTSConfig


def test_default_config():
    """测试默认配置"""
    config = TTSConfig()
    assert config.primary_provider == "edge-tts"
    assert config.failure_threshold == 5
    assert config.cooldown_seconds == 300


def test_config_from_env(monkeypatch):
    """测试从环境变量加载配置"""
    monkeypatch.setenv("TTS_FAILURE_THRESHOLD", "10")
    monkeypatch.setenv("TTS_COOLDOWN_SECONDS", "600")

    config = TTSConfig()
    assert config.failure_threshold == 10
    assert config.cooldown_seconds == 600
