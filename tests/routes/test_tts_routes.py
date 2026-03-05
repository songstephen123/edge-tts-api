"""
TTS 路由测试
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_list_providers():
    """测试列出提供者"""
    client = TestClient(app)
    response = client.get("/tts/providers")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert len(data["providers"]) > 0
    assert data["providers"][0]["name"] == "EdgeTTSProvider"


def test_get_stats():
    """测试获取统计信息"""
    client = TestClient(app)
    response = client.get("/tts/stats")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert "total_providers" in data
