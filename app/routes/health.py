"""
健康检查路由
"""
from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
import logging

from app.models.schemas import HealthResponse
from app.services.edge_tts import tts_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=HealthResponse)
@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    健康检查端点

    Returns:
        服务状态信息
    """
    try:
        # 测试 Edge TTS 是否可用
        voices = await tts_service.list_voices()
        edge_tts_available = len(voices) > 0

        return HealthResponse(
            status="healthy" if edge_tts_available else "degraded",
            service="edge-tts-service",
            version="1.0.0",
            edge_tts_available=edge_tts_available
        )

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "edge-tts-service",
                "version": "1.0.0",
                "edge_tts_available": False,
                "error": str(e)
            }
        )
