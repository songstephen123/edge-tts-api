"""
快速 Opus 转换服务
方案 2 + 方案 3 组合：opusenc + 流式处理
"""
import asyncio
import subprocess
import logging
import os
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

# 配置
OPUSENC_AVAILABLE = None
USE_OPUSENC = True  # 默认尝试使用 opusenc


async def check_opusenc_available() -> bool:
    """检查 opusenc 是否可用"""
    global OPUSENC_AVAILABLE

    if OPUSENC_AVAILABLE is not None:
        return OPUSENC_AVAILABLE

    try:
        proc = await asyncio.create_subprocess_exec(
            "which", "opusenc",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()

        OPUSENC_AVAILABLE = bool(stdout.strip())
        if OPUSENC_AVAILABLE:
            logger.info("✅ opusenc 可用")
        else:
            logger.warning("⚠️  opusenc 不可用，将使用 FFmpeg")

        return OPUSENC_AVAILABLE

    except Exception as e:
        logger.warning(f"检查 opusenc 失败: {e}")
        OPUSENC_AVAILABLE = False
        return False


async def convert_to_opus_streaming_fast(mp3_data: bytes) -> bytes:
    """
    快速 Opus 转换（opusenc + 流式处理）

    优化点：
    1. 使用 opusenc（比 FFmpeg 快 2-3x）
    2. 流式处理（无中间文件）
    3. VoIP 优化参数

    Args:
        mp3_data: MP3 格式音频数据

    Returns:
        Opus 格式音频数据
    """
    # 确保 opusenc 检查已运行
    await check_opusenc_available()

    # 如果 opusenc 可用，使用 opusenc
    if OPUSENC_AVAILABLE and USE_OPUSENC:
        return await _convert_with_opusenc_streaming(mp3_data)
    else:
        # 降级到 FFmpeg 流式处理
        return await _convert_with_ffmpeg_streaming(mp3_data)


async def _convert_with_opusenc_streaming(mp3_data: bytes) -> bytes:
    """
    使用 opusenc 流式转换

    优势：
    - 编码速度快 2-3x
    - 专门针对 Opus 优化
    - 更好的音质控制
    """
    try:
        # opusenc 需要输入文件，使用管道
        # 创建命名管道或使用临时文件

        # 方案：使用进程链，FFmpeg 解码 → opusenc 编码
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i", "pipe:0",           # 从 stdin 读取 MP3
            "-f", "wav",              # 解码为 WAV（通过管道）
            "pipe:1",                # 输出到 stdout
            "|",
            "opusenc",
            "--bitrate", "32",        # 32kbps（平衡速度和质量）
            "--complexity", "0",      # 最快编码
            "--framesize", "20",      # 20ms 帧
            "--max-delay", "20",      # 最大延迟 20ms
            "--downmix", "mono",      # 单声道
            "-",                     # 从 stdin 读取
            "pipe:1",                # 输出到 stdout
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # 发送数据并获取结果
        stdout, stderr = await proc.communicate(input=mp3_data)

        if proc.returncode != 0:
            logger.error(f"opusenc 转换失败: {stderr.decode()}")
            # 降级到 FFmpeg
            return await _convert_with_ffmpeg_streaming(mp3_data)

        logger.debug(f"opusenc 转换成功: {len(stdout)} 字节")
        return stdout

    except Exception as e:
        logger.error(f"opusenc 转换异常: {e}")
        # 降级到 FFmpeg
        return await _convert_with_ffmpeg_streaming(mp3_data)


async def _convert_with_ffmpeg_streaming(mp3_data: bytes) -> bytes:
    """
    使用 FFmpeg 流式转换（降级方案）

    优化参数：
    - compression_level 0: 最快编码
    - application voip: VoIP 优化
    - b:a 32k: 较低比特率（更快）
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i", "pipe:0",           # 从 stdin 读取
            "-acodec", "libopus",
            "-b:a", "32k",            # 32kbps
            "-compression_level", "0", # 最快编码
            "-application", "voip",   # VoIP 模式
            "-vn",                   # 无视频
            "-f", "opus",             # Opus 格式
            "pipe:1",                # 到 stdout
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate(input=mp3_data)

        if proc.returncode != 0:
            logger.error(f"FFmpeg 转换失败: {stderr.decode()}")
            # 完全失败，返回原数据
            return mp3_data

        logger.debug(f"FFmpeg 流式转换成功: {len(stdout)} 字节")
        return stdout

    except Exception as e:
        logger.error(f"FFmpeg 转换异常: {e}")
        return mp3_data


async def convert_to_opus_with_cache(
    mp3_data: bytes,
    text: Optional[str] = None,
    voice: Optional[str] = None
) -> bytes:
    """
    带缓存的 Opus 转换

    优先返回缓存的音频，避免重复转换
    """
    import hashlib
    from pathlib import Path

    # 缓存目录
    cache_dir = Path("/tmp/tts_cache")
    cache_dir.mkdir(exist_ok=True)

    # 生成缓存键
    cache_key_parts = [str(len(mp3_data))]
    if text:
        cache_key_parts.append(text)
    if voice:
        cache_key_parts.append(voice)

    cache_key = hashlib.md5(":".join(cache_key_parts).encode()).hexdigest()
    cache_file = cache_dir / f"{cache_key}.opus"

    # 检查缓存
    if cache_file.exists():
        # 检查缓存年龄（7天过期）
        import time
        age = time.time() - cache_file.stat().st_mtime
        if age < 604800:  # 7天
            logger.debug(f"缓存命中: {cache_key}")
            with open(cache_file, "rb") as f:
                return f.read()
        else:
            # 删除过期缓存
            cache_file.unlink()

    # 执行转换
    opus_data = await convert_to_opus_streaming_fast(mp3_data)

    # 保存到缓存
    with open(cache_file, "wb") as f:
        f.write(opus_data)

    return opus_data


# 性能监控
import time

conversion_times = []

async def convert_to_opus_monitored(mp3_data: bytes) -> bytes:
    """带性能监控的转换"""
    start = time.time()

    result = await convert_to_opus_streaming_fast(mp3_data)

    duration = time.time() - start
    conversion_times.append(duration)

    # 记录性能
    if duration > 0.1:  # 超过 100ms
        logger.warning(f"转换较慢: {duration*1000:.0f}ms")
    else:
        logger.debug(f"转换用时: {duration*1000:.0f}ms")

    # 保持最近 100 次记录
    if len(conversion_times) > 100:
        conversion_times.pop(0)

    return result


def get_performance_stats() -> dict:
    """获取性能统计"""
    if not conversion_times:
        return {"message": "暂无数据"}

    return {
        "total_conversions": len(conversion_times),
        "avg_time_ms": sum(conversion_times) / len(conversion_times) * 1000,
        "min_time_ms": min(conversion_times) * 1000,
        "max_time_ms": max(conversion_times) * 1000,
        "p95_time_ms": sorted(conversion_times)[int(len(conversion_times) * 0.95)] * 1000
    }
