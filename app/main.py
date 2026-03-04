"""
Edge TTS Service - Main Application
基于微软 Edge TTS 的文本转语音 API 服务
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import logging
from contextlib import asynccontextmanager
import io

from app.config import settings
from app.routes import tts, health, voices

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 Edge TTS Service 启动中...")
    yield
    logger.info("👋 Edge TTS Service 已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="Edge TTS Service",
    description="基于微软 Edge TTS 的文本转语音 API 服务 - 完全免费，无需 API Key",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "内部服务器错误",
            "detail": str(exc) if settings.LOG_LEVEL == "DEBUG" else None
        }
    )


# 注册路由
app.include_router(health.router, prefix="/health", tags=["健康检查"])
app.include_router(tts.router, prefix="/tts", tags=["文本转语音"])
app.include_router(voices.router, prefix="/voices", tags=["音色管理"])


# 根路径
@app.get("/")
async def root():
    """根路径 - 服务信息"""
    return {
        "service": "Edge TTS Service",
        "version": "1.0.0",
        "description": "基于微软 Edge TTS 的文本转语音 API 服务",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "tts": "POST /tts - 文本转语音",
            "voices": "GET /voices - 获取音色列表",
            "health": "GET /health - 健康检查"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=True
    )
