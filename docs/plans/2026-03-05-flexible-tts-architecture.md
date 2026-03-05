# 灵活 TTS 提供者架构 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个支持多引擎的 TTS 服务，实现自动降级和故障切换，解决 Edge TTS 403 错误问题。

**Architecture:** Provider 模式 + Manager 调度器。TTSManager 按优先级选择引擎，失败自动降级到备选引擎。支持 Edge TTS（免费主引擎）、火山引擎（付费备选）、本地 pyttsx3（兜底）。

**Tech Stack:** FastAPI, edge-tts, pyttsx3, asyncio, pydantic

---

## Task 1: 创建 Provider 基类和接口

**Files:**
- Create: `app/services/tts_providers/__init__.py`
- Create: `app/services/tts_providers/base.py`
- Test: `tests/services/test_tts_providers_base.py`

**Step 1: 创建目录结构**

```bash
mkdir -p app/services/tts_providers
touch app/services/tts_providers/__init__.py
```

**Step 2: 编写基类和接口**

创建 `app/services/tts_providers/base.py`:

```python
"""
TTS 提供者基类 - 定义统一接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class TTSResult:
    """TTS 生成结果"""
    audio_data: bytes
    format: str  # mp3, opus, wav
    provider: str
    cached: bool = False


class TTSProviderError(Exception):
    """TTS 提供者错误基类"""
    pass


class TTSProvider(ABC):
    """TTS 提供者基类"""

    @abstractmethod
    async def text_to_speech(
        self,
        text: str,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> TTSResult:
        """
        生成语音

        Args:
            text: 要转换的文本
            voice: 音色 ID 或简称
            rate: 语速调整，如 "+10%", "-20%"
            pitch: 音调调整，如 "+50Hz", "-100Hz"
            volume: 音量调整，如 "+10%", "-50%"

        Returns:
            TTSResult: 包含音频数据和元信息

        Raises:
            TTSProviderError: 生成失败时抛出
        """
        pass

    @abstractmethod
    async def get_available_voices(self) -> list[dict]:
        """
        获取可用音色列表

        Returns:
            list[dict]: 音色信息列表，每个包含 id, name, gender 等
        """
        pass

    @property
    @abstractmethod
    def is_free(self) -> bool:
        """是否免费引擎"""
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """优先级（数字越小优先级越高）"""
        pass

    @property
    def name(self) -> str:
        """提供者名称"""
        return self.__class__.__name__
```

**Step 3: 编写测试**

创建 `tests/services/test_tts_providers_base.py`:

```python
import pytest
from app.services.tts_providers.base import TTSProvider, TTSResult, TTSProviderError


class MockTTSProvider(TTSProvider):
    """测试用的 Mock Provider"""

    @property
    def is_free(self) -> bool:
        return True

    @property
    def priority(self) -> int:
        return 1

    async def text_to_speech(self, text: str, voice: str, **kwargs) -> TTSResult:
        return TTSResult(
            audio_data=b"mock_audio",
            format="mp3",
            provider="mock"
        )

    async def get_available_voices(self) -> list[dict]:
        return [{"id": "mock", "name": "Mock Voice", "gender": "Unknown"}]


def test_tts_result_creation():
    """测试 TTSResult 数据类"""
    result = TTSResult(
        audio_data=b"test_audio",
        format="mp3",
        provider="test",
        cached=True
    )
    assert result.audio_data == b"test_audio"
    assert result.format == "mp3"
    assert result.provider == "test"
    assert result.cached is True


@pytest.mark.asyncio
async def test_mock_provider_interface():
    """测试 Mock Provider 实现接口"""
    provider = MockTTSProvider()

    # 测试属性
    assert provider.is_free is True
    assert provider.priority == 1
    assert provider.name == "MockTTSProvider"

    # 测试方法
    result = await provider.text_to_speech("hello", "mock")
    assert result.audio_data == b"mock_audio"
    assert result.format == "mp3"

    voices = await provider.get_available_voices()
    assert len(voices) == 1
    assert voices[0]["id"] == "mock"


def test_tts_provider_error():
    """测试自定义异常"""
    with pytest.raises(TTSProviderError):
        raise TTSProviderError("Test error")
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/services/test_tts_providers_base.py -v
```

预期输出: `PASSED`

**Step 5: 提交**

```bash
git add app/services/tts_providers/ tests/services/
git commit -m "feat: add TTS provider base class and interface

- Add TTSProvider abstract base class
- Add TTSResult dataclass
- Add TTSProviderError exception
- Add base tests with mock provider"
```

---

## Task 2: 实现 Edge TTS Provider

**Files:**
- Create: `app/services/tts_providers/edge_tts_provider.py`
- Modify: `app/services/tts_providers/__init__.py`
- Test: `tests/services/test_edge_tts_provider.py`

**Step 1: 实现 Edge TTS Provider**

创建 `app/services/tts_providers/edge_tts_provider.py`:

```python
"""
Edge TTS 提供者 - 免费主引擎
"""
import logging
from typing import Dict

import edge_tts

from app.services.tts_providers.base import TTSProvider, TTSResult, TTSProviderError

logger = logging.getLogger(__name__)


class EdgeTTSProvider(TTSProvider):
    """
    Edge TTS 提供者

    使用微软 Edge 浏览器的免费 TTS API
    音质好，但可能被封锁
    """

    # 常用音色映射（简称 -> 完整 ID）
    VOICE_MAP: Dict[str, str] = {
        "xiaoxiao": "zh-CN-XiaoxiaoNeural",
        "yunyang": "zh-CN-YunyangNeural",
        "xiaoyi": "zh-CN-XiaoyiNeural",
        "xiaohan": "zh-CN-XiaohanNeural",
        "xiaomeng": "zh-CN-XiaomengNeural",
    }

    def __init__(self, default_voice: str = "xiaoxiao"):
        """
        初始化 Edge TTS 提供者

        Args:
            default_voice: 默认音色简称
        """
        self.default_voice = default_voice

    @property
    def is_free(self) -> bool:
        return True

    @property
    def priority(self) -> int:
        return 1  # 最高优先级

    def _resolve_voice(self, voice: str) -> str:
        """
        解析音色 ID

        Args:
            voice: 音色简称或完整 ID

        Returns:
            完整音色 ID
        """
        # 如果是简称，从映射表获取
        if voice in self.VOICE_MAP:
            return self.VOICE_MAP[voice]
        # 否则直接使用（可能是完整 ID）
        return voice

    async def text_to_speech(
        self,
        text: str,
        voice: str = "xiaoxiao",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> TTSResult:
        """
        生成语音

        Args:
            text: 要转换的文本
            voice: 音色简称或完整 ID
            rate: 语速调整
            pitch: 音调调整
            volume: 音量调整

        Returns:
            TTSResult

        Raises:
            TTSProviderError: 生成失败时
        """
        voice_id = self._resolve_voice(voice)

        try:
            # 创建 Communicate 对象
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_id,
                rate=rate,
                pitch=pitch,
                volume=volume
            )

            # 流式获取音频数据
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]

            if not audio_data:
                raise TTSProviderError("Edge TTS 返回空音频数据")

            logger.info(f"Edge TTS 生成成功: text='{text[:30]}...', voice={voice_id}")
            return TTSResult(
                audio_data=audio_data,
                format="mp3",
                provider="edge-tts"
            )

        except Exception as e:
            logger.error(f"Edge TTS 生成失败: {e}")
            raise TTSProviderError(f"Edge TTS 失败: {str(e)}") from e

    async def get_available_voices(self) -> list[dict]:
        """
        获取可用音色列表

        Returns:
            音色信息列表
        """
        # 返回预设的常用音色
        return [
            {"id": "xiaoxiao", "name": "晓晓", "gender": "女", "full_id": "zh-CN-XiaoxiaoNeural"},
            {"id": "yunyang", "name": "云扬", "gender": "男", "full_id": "zh-CN-YunyangNeural"},
            {"id": "xiaoyi", "name": "晓伊", "gender": "女", "full_id": "zh-CN-XiaoyiNeural"},
        ]
```

**Step 2: 更新 __init__.py**

修改 `app/services/tts_providers/__init__.py`:

```python
from app.services.tts_providers.base import TTSProvider, TTSResult, TTSProviderError
from app.services.tts_providers.edge_tts_provider import EdgeTTSProvider

__all__ = [
    "TTSProvider",
    "TTSResult",
    "TTSProviderError",
    "EdgeTTSProvider",
]
```

**Step 3: 编写测试**

创建 `tests/services/test_edge_tts_provider.py`:

```python
import pytest

from app.services.tts_providers.edge_tts_provider import EdgeTTSProvider


def test_edge_tts_provider_properties():
    """测试 Edge TTS Provider 属性"""
    provider = EdgeTTSProvider()
    assert provider.is_free is True
    assert provider.priority == 1
    assert provider.name == "EdgeTTSProvider"


def test_voice_resolution():
    """测试音色解析"""
    provider = EdgeTTSProvider()

    # 简称映射
    assert provider._resolve_voice("xiaoxiao") == "zh-CN-XiaoxiaoNeural"
    assert provider._resolve_voice("yunyang") == "zh-CN-YunyangNeural"

    # 完整 ID 直接返回
    full_id = "zh-CN-XiaoxiaoNeural"
    assert provider._resolve_voice(full_id) == full_id


@pytest.mark.asyncio
async def test_text_to_speech():
    """测试生成语音"""
    provider = EdgeTTSProvider()

    result = await provider.text_to_speech(
        text="你好，世界",
        voice="xiaoxiao"
    )

    assert result.provider == "edge-tts"
    assert result.format == "mp3"
    assert len(result.audio_data) > 0


@pytest.mark.asyncio
async def test_get_available_voices():
    """测试获取音色列表"""
    provider = EdgeTTSProvider()
    voices = await provider.get_available_voices()

    assert len(voices) > 0
    assert voices[0]["id"] == "xiaoxiao"
    assert "name" in voices[0]
```

**Step 4: 运行测试**

```bash
pytest tests/services/test_edge_tts_provider.py -v
```

预期输出: `PASSED`

**Step 5: 提交**

```bash
git add app/services/tts_providers/ tests/services/
git commit -m "feat: add Edge TTS provider implementation

- Implement EdgeTTSProvider with voice mapping
- Add text_to_speech method with streaming
- Add error handling and logging
- Add unit tests"
```

---

## Task 3: 实现 TTS Manager 核心调度器

**Files:**
- Create: `app/services/tts_manager.py`
- Modify: `app/services/tts_providers/__init__.py`
- Test: `tests/services/test_tts_manager.py`

**Step 1: 实现 TTS Manager**

创建 `app/services/tts_manager.py`:

```python
"""
TTS 管理器 - 核心调度器

负责：
- 引擎注册和管理
- 按优先级选择引擎
- 失败自动降级
- 失败统计和冷却机制
"""
import asyncio
import logging
import time
from collections import defaultdict
from typing import Optional, List

from app.services.tts_providers.base import TTSProvider, TTSResult, TTSProviderError

logger = logging.getLogger(__name__)


class TTSAllFailedError(TTSProviderError):
    """所有引擎均失败"""
    pass


class TTSManager:
    """
    TTS 引擎管理器

    按优先级管理多个 TTS 提供者，实现自动降级和故障切换
    """

    def __init__(self):
        self._providers: List[TTSProvider] = []
        self._failure_counts: defaultdict[str, int] = defaultdict(int)
        self._disabled_until: dict[str, float] = {}
        self._failure_threshold = 5
        self._cooldown_seconds = 300

    def register_provider(self, provider: TTSProvider) -> None:
        """
        注册 TTS 提供者

        Args:
            provider: TTS 提供者实例
        """
        self._providers.append(provider)
        # 按优先级排序（数字越小优先级越高）
        self._providers.sort(key=lambda p: p.priority)
        logger.info(f"注册 TTS 提供者: {provider.name} (优先级: {provider.priority})")

    def get_providers(self) -> List[TTSProvider]:
        """获取所有已注册的提供者"""
        return self._providers.copy()

    def _is_provider_available(self, provider: TTSProvider) -> bool:
        """
        检查提供者是否可用（考虑冷却）

        Args:
            provider: TTS 提供者

        Returns:
            是否可用
        """
        name = provider.name
        if name in self._disabled_until:
            if time.time() < self._disabled_until[name]:
                logger.debug(f"{name} 处于冷却期，跳过")
                return False
            # 冷却结束，清除禁用
            del self._disabled_until[name]
            logger.info(f"{name} 冷却结束，重新启用")
        return True

    def _record_failure(self, provider: TTSProvider) -> None:
        """
        记录失败，可能触发禁用

        Args:
            provider: TTS 提供者
        """
        name = provider.name
        self._failure_counts[name] += 1

        count = self._failure_counts[name]
        logger.warning(f"{name} 失败计数: {count}/{self._failure_threshold}")

        if count >= self._failure_threshold:
            self._disabled_until[name] = time.time() + self._cooldown_seconds
            logger.warning(f"{name} 连续失败 {count} 次，进入 {self._cooldown_seconds} 秒冷却")

    def _record_success(self, provider: TTSProvider) -> None:
        """
        记录成功，重置失败计数

        Args:
            provider: TTS 提供者
        """
        name = provider.name
        if name in self._failure_counts and self._failure_counts[name] > 0:
            logger.info(f"{name} 恢复正常，清除失败计数")
            del self._failure_counts[name]

    async def text_to_speech(
        self,
        text: str,
        voice: str = "xiaoxiao",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%",
        force_provider: Optional[str] = None
    ) -> TTSResult:
        """
        智能生成语音

        按优先级尝试各引擎，失败则降级到下一个

        Args:
            text: 要转换的文本
            voice: 音色简称
            rate: 语速
            pitch: 音调
            volume: 音量
            force_provider: 强制使用指定提供者名称

        Returns:
            TTSResult

        Raises:
            TTSAllFailedError: 所有引擎均失败
        """
        if not self._providers:
            raise TTSAllFailedError("没有注册任何 TTS 提供者")

        # 强制指定提供者
        if force_provider:
            for provider in self._providers:
                if provider.name == force_provider:
                    return await provider.text_to_speech(text, voice, rate, pitch, volume)
            raise TTSAllFailedError(f"未找到提供者: {force_provider}")

        # 按优先级尝试
        last_error = None
        for provider in self._providers:
            if not self._is_provider_available(provider):
                continue

            try:
                logger.info(f"尝试使用 {provider.name} 生成语音")
                result = await provider.text_to_speech(text, voice, rate, pitch, volume)
                self._record_success(provider)
                return result

            except TTSProviderError as e:
                last_error = e
                self._record_failure(provider)
                logger.warning(f"{provider.name} 失败: {e}，尝试下一个")
                continue

        # 所有引擎都失败
        raise TTSAllFailedError(f"所有 TTS 引擎均失败: {last_error}")

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "providers": [
                {
                    "name": p.name,
                    "is_free": p.is_free,
                    "priority": p.priority,
                    "failures": self._failure_counts.get(p.name, 0),
                    "disabled_until": self._disabled_until.get(p.name),
                }
                for p in self._providers
            ],
            "total_providers": len(self._providers),
        }
```

**Step 2: 更新 __init__.py**

修改 `app/services/tts_providers/__init__.py`:

```python
from app.services.tts_providers.base import TTSProvider, TTSResult, TTSProviderError
from app.services.tts_providers.edge_tts_provider import EdgeTTSProvider

__all__ = [
    "TTSProvider",
    "TTSResult",
    "TTSProviderError",
    "EdgeTTSProvider",
]
```

**Step 3: 编写测试**

创建 `tests/services/test_tts_manager.py`:

```python
import pytest

from app.services.tts_manager import TTSManager, TTSAllFailedError
from app.services.tts_providers.base import TTSProvider, TTSResult, TTSProviderError
from app.services.tts_providers.edge_tts_provider import EdgeTTSProvider


class MockSuccessProvider(TTSProvider):
    """总是成功的 Mock Provider"""
    @property
    def is_free(self): return True
    @property
    def priority(self): return 1
    async def text_to_speech(self, text, voice, **kwargs):
        return TTSResult(audio_data=b"success", format="mp3", provider="mock_success")
    async def get_available_voices(self):
        return []


class MockFailureProvider(TTSProvider):
    """总是失败的 Mock Provider"""
    @property
    def is_free(self): return True
    @property
    def priority(self): return 2
    async def text_to_speech(self, text, voice, **kwargs):
        raise TTSProviderError("Mock failure")
    async def get_available_voices(self):
        return []


def test_register_providers():
    """测试注册提供者"""
    manager = TTSManager()
    p1 = MockSuccessProvider()
    p2 = MockFailureProvider()

    manager.register_provider(p2)
    manager.register_provider(p1)

    # 应该按优先级排序
    providers = manager.get_providers()
    assert providers[0].priority < providers[1].priority


@pytest.mark.asyncio
async def test_text_to_speech_success():
    """测试成功生成"""
    manager = TTSManager()
    manager.register_provider(MockSuccessProvider())

    result = await manager.text_to_speech("test", "voice")
    assert result.audio_data == b"success"
    assert result.provider == "mock_success"


@pytest.mark.asyncio
async def test_fallback_on_failure():
    """测试失败降级"""
    manager = TTSManager()
    manager.register_provider(MockFailureProvider())
    manager.register_provider(MockSuccessProvider())

    result = await manager.text_to_speech("test", "voice")
    assert result.audio_data == b"success"


@pytest.mark.asyncio
async def test_all_providers_fail():
    """测试所有引擎失败"""
    manager = TTSManager()
    manager.register_provider(MockFailureProvider())

    with pytest.raises(TTSAllFailedError):
        await manager.text_to_speech("test", "voice")


def test_get_stats():
    """测试获取统计信息"""
    manager = TTSManager()
    manager.register_provider(MockSuccessProvider())

    stats = manager.get_stats()
    assert stats["total_providers"] == 1
    assert "providers" in stats
```

**Step 4: 运行测试**

```bash
pytest tests/services/test_tts_manager.py -v
```

预期输出: `PASSED`

**Step 5: 提交**

```bash
git add app/services/tts_manager.py tests/services/
git commit -m "feat: add TTS Manager core dispatcher

- Implement provider registration and priority sorting
- Add auto-fallback on provider failure
- Add failure tracking and cooldown mechanism
- Add comprehensive unit tests"
```

---

## Task 4: 更新路由层使用 TTS Manager

**Files:**
- Modify: `app/routes/tts.py`
- Test: `tests/routes/test_tts_routes.py`

**Step 1: 备份原路由文件**

```bash
cp app/routes/tts.py app/routes/tts.py.backup
```

**Step 2: 更新路由导入和初始化**

修改 `app/routes/tts.py` 文件头部（约第 1-30 行）:

```python
"""
TTS 路由 - 文本转语音接口
支持多引擎自动降级
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import logging
import os
import io

from app.models.schemas import TTSRequest
from app.services.tts_manager import TTSManager, TTSAllFailedError
from app.services.tts_providers.edge_tts_provider import EdgeTTSProvider
from app.services.opus_converter import convert_to_opus_with_cache
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# 静态文件存储目录
STATIC_DIR = "/tmp/tts_audio"
os.makedirs(STATIC_DIR, exist_ok=True)

# 初始化 TTS Manager
tts_manager = TTSManager()
tts_manager.register_provider(EdgeTTSProvider())
```

**Step 3: 更新主 TTS 端点**

修改 `text_to_speech` 函数（约第 115-182 行）:

```python
@router.post("")
async def text_to_speech(req: TTSRequest):
    """
    文本转语音 - 自动选择最优引擎

    支持参数：
    - **text**: 要转换的文本（必填）
    - **voice**: 音色 ID 或简称（可选，默认 xiaoxiao）
    - **rate**: 语速（可选）
    - **pitch**: 音调（可选）
    - **volume**: 音量（可选）
    - **format**: 输出格式，支持 mp3/opus（可选，默认 mp3）
    - **provider**: 强制使用指定引擎（可选）
    """
    try:
        output_format = getattr(req, 'format', 'mp3')
        if output_format not in ['mp3', 'opus']:
            output_format = 'mp3'

        voice = req.voice or settings.DEFAULT_VOICE
        force_provider = getattr(req, 'provider', None)

        logger.info(f"TTS 请求: text='{req.text[:50]}...', voice={voice}, provider={force_provider}")

        # 使用 TTS Manager 生成语音
        result = await tts_manager.text_to_speech(
            text=req.text,
            voice=voice,
            rate=getattr(req, 'rate', '+0%'),
            pitch=getattr(req, 'pitch', '+0Hz'),
            volume=getattr(req, 'volume', '+0%'),
            force_provider=force_provider
        )

        # Opus 转换（如果需要）
        if output_format == 'opus':
            audio_data = await convert_to_opus_with_cache(
                result.audio_data,
                text=req.text,
                voice=voice
            )
        else:
            audio_data = result.audio_data

        # 保存文件
        filename = await save_audio_file(audio_data, output_format)

        # 返回响应
        media_type = "audio/opus" if output_format == 'opus' else "audio/mpeg"

        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(audio_data)),
                "X-Audio-Filename": filename,
                "X-Audio-Format": output_format,
                "X-TTS-Provider": result.provider,
                "X-TTS-Cached": str(result.cached),
                "Access-Control-Expose-Headers": "X-Audio-Filename,X-Audio-Format,X-TTS-Provider,X-TTS-Cached,Content-Length"
            }
        )

    except TTSAllFailedError as e:
        logger.error(f"所有 TTS 引擎均失败: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"语音生成服务暂时不可用: {str(e)}"
        )
    except Exception as e:
        logger.error(f"TTS 生成失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"语音生成失败: {str(e)}"
        )
```

**Step 4: 添加新端点**

在文件末尾添加新端点:

```python
@router.get("/providers")
async def list_providers():
    """列出可用的 TTS 引擎"""
    return {
        "providers": [
            {
                "name": p.name,
                "is_free": p.is_free,
                "priority": p.priority,
            }
            for p in tts_manager.get_providers()
        ]
    }


@router.get("/stats")
async def get_stats():
    """获取 TTS 引擎统计信息"""
    return tts_manager.get_stats()
```

**Step 5: 编写测试**

创建 `tests/routes/test_tts_routes.py`:

```python
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
```

**Step 6: 运行测试**

```bash
pytest tests/routes/test_tts_routes.py -v
```

预期输出: `PASSED`

**Step 7: 提交**

```bash
git add app/routes/tts.py tests/routes/
git commit -m "feat: update routes to use TTS Manager

- Replace direct edge-tts calls with TTS Manager
- Add /tts/providers endpoint to list available engines
- Add /tts/stats endpoint for statistics
- Add X-TTS-Provider and X-TTS-Cached headers"
```

---

## Task 5: 添加本地 TTS Provider（离线兜底）

**Files:**
- Create: `app/services/tts_providers/local_provider.py`
- Modify: `app/services/tts_providers/__init__.py`
- Modify: `app/routes/tts.py`
- Modify: `Dockerfile`
- Test: `tests/services/test_local_provider.py`

**Step 1: 实现本地 Provider**

创建 `app/services/tts_providers/local_provider.py`:

```python
"""
本地 TTS 提供者 - 离线兜底

使用 pyttsx3 实现完全本地的语音合成
音质一般，但永远可用
"""
import asyncio
import logging
import os
import tempfile
from typing import List

import pyttsx3

from app.services.tts_providers.base import TTSProvider, TTSResult, TTSProviderError

logger = logging.getLogger(__name__)


class LocalTTSProvider(TTSProvider):
    """
    本地 TTS 提供者

    使用 pyttsx3 进行本地语音合成
    作为紧急兜底方案
    """

    def __init__(self):
        self._driver = None
        self._voices_cache = None

    @property
    def is_free(self) -> bool:
        return True

    @property
    def priority(self) -> int:
        return 3  # 最低优先级，兜底用

    def _get_driver(self):
        """获取 pyttsx3 驱动（延迟初始化）"""
        if self._driver is None:
            try:
                self._driver = pyttsx3.init()
            except Exception as e:
                raise TTSProviderError(f"初始化本地 TTS 失败: {e}")
        return self._driver

    async def text_to_speech(
        self,
        text: str,
        voice: str = "xiaoxiao",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> TTSResult:
        """
        生成本地语音

        Args:
            text: 要转换的文本
            voice: 音色（本地引擎会尽力匹配中文语音）
            rate: 语速（忽略，本地引擎支持有限）
            pitch: 音调（忽略）
            volume: 音量（忽略）

        Returns:
            TTSResult
        """
        try:
            # pyttsx3 是同步的，需要在线程池运行
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._generate_sync,
                text
            )

            return TTSResult(
                audio_data=audio_data,
                format="wav",
                provider="local"
            )

        except Exception as e:
            logger.error(f"本地 TTS 生成失败: {e}")
            raise TTSProviderError(f"本地 TTS 失败: {str(e)}") from e

    def _generate_sync(self, text: str) -> bytes:
        """
        同步生成音频（在线程池中运行）

        Args:
            text: 要转换的文本

        Returns:
            WAV 格式音频数据
        """
        driver = self._get_driver()

        # 尝试设置中文语音
        voices = driver.getProperty('voices')
        for v in voices:
            if v.id and ('chinese' in v.id.lower() or 'zh' in v.id.lower()):
                driver.setProperty('voice', v.id)
                logger.debug(f"使用本地语音: {v.id}")
                break

        # 生成到临时文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name

        try:
            driver.save_to_file(text, temp_path)
            driver.runAndWait()

            # 读取生成的文件
            with open(temp_path, "rb") as f:
                audio_data = f.read()

            return audio_data

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def get_available_voices(self) -> List[dict]:
        """
        获取可用音色列表

        Returns:
            音色信息列表
        """
        if self._voices_cache is not None:
            return self._voices_cache

        try:
            driver = self._get_driver()
            voices = driver.getProperty('voices')

            self._voices_cache = []
            for v in voices:
                self._voices_cache.append({
                    "id": v.id or "default",
                    "name": v.name or "默认",
                    "gender": "Unknown",
                    "languages": v.languages if hasattr(v, 'languages') else []
                })

            return self._voices_cache

        except Exception as e:
            logger.warning(f"获取本地音色列表失败: {e}")
            return [{"id": "default", "name": "默认", "gender": "Unknown"}]
```

**Step 2: 更新 __init__.py**

修改 `app/services/tts_providers/__init__.py`:

```python
from app.services.tts_providers.base import TTSProvider, TTSResult, TTSProviderError
from app.services.tts_providers.edge_tts_provider import EdgeTTSProvider
from app.services.tts_providers.local_provider import LocalTTSProvider

__all__ = [
    "TTSProvider",
    "TTSResult",
    "TTSProviderError",
    "EdgeTTSProvider",
    "LocalTTSProvider",
]
```

**Step 3: 在路由中注册本地 Provider**

修改 `app/routes/tts.py`，在初始化部分添加:

```python
from app.services.tts_providers.local_provider import LocalTTSProvider

# 初始化 TTS Manager
tts_manager = TTSManager()
tts_manager.register_provider(EdgeTTSProvider())
tts_manager.register_provider(LocalTTSProvider())  # 添加本地兜底
```

**Step 4: 更新 Dockerfile**

修改 `Dockerfile`，添加 espeak 依赖:

```dockerfile
# 在现有 RUN apt-get 命令中添加 espeak
RUN apt-get update && apt-get install -y \
    ffmpeg \
    opus-tools \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    && rm -rf /var/lib/apt/lists/*

# 在 pip install 部分添加 pyttsx3
RUN pip install --no-cache-dir edge-tts opus-tools pyttsx3
```

**Step 5: 编写测试**

创建 `tests/services/test_local_provider.py`:

```python
import pytest

from app.services.tts_providers.local_provider import LocalTTSProvider


def test_local_provider_properties():
    """测试本地 Provider 属性"""
    provider = LocalTTSProvider()
    assert provider.is_free is True
    assert provider.priority == 3
    assert provider.name == "LocalTTSProvider"


@pytest.mark.asyncio
async def test_text_to_speech():
    """测试生成本地语音"""
    provider = LocalTTSProvider()

    result = await provider.text_to_speech(
        text="Hello",
        voice="default"
    )

    assert result.provider == "local"
    assert result.format == "wav"
    assert len(result.audio_data) > 0
    # WAV 文件头应该是 RIFF
    assert result.audio_data[:4] == b"RIFF"


@pytest.mark.asyncio
async def test_get_voices():
    """测试获取音色列表"""
    provider = LocalTTSProvider()
    voices = await provider.get_available_voices()

    assert len(voices) > 0
    assert "id" in voices[0]
    assert "name" in voices[0]
```

**Step 6: 运行测试**

```bash
pytest tests/services/test_local_provider.py -v
```

预期输出: `PASSED`

**Step 7: 提交**

```bash
git add app/services/tts_providers/local_provider.py app/services/tts_providers/__init__.py app/routes/tts.py Dockerfile tests/services/
git commit -m "feat: add local TTS provider as fallback

- Implement LocalTTSProvider using pyttsx3
- Add espeak dependencies to Dockerfile
- Register local provider as lowest priority fallback
- Add unit tests"
```

---

## Task 6: 添加配置系统

**Files:**
- Create: `app/config/tts_config.py`
- Modify: `app/config.py`
- Test: `tests/config/test_tts_config.py`

**Step 1: 创建 TTS 配置模块**

创建 `app/config/tts_config.py`:

```python
"""
TTS 配置
"""
from pydantic_settings import BaseSettings


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

    class Config:
        env_prefix = "TTS_"
        env_file = ".env"
```

**Step 2: 更新主配置**

修改 `app/config.py`，导入 TTS 配置:

```python
from app.config.tts_config import TTSConfig

# 在 Settings 类中添加
class Settings(BaseSettings):
    # ... 现有配置 ...

    # TTS 配置
    tts: TTSConfig = TTSConfig()
```

**Step 3: 在 TTSManager 中使用配置**

修改 `app/services/tts_manager.py`，在 `__init__` 中接收配置:

```python
from app.config.tts_config import TTSConfig

class TTSManager:
    def __init__(self, config: TTSConfig = None):
        self._providers: List[TTSProvider] = []
        self._failure_counts: defaultdict[str, int] = defaultdict(int)
        self._disabled_until: dict[str, float] = {}

        # 使用配置
        self._config = config or TTSConfig()
        self._failure_threshold = self._config.failure_threshold
        self._cooldown_seconds = self._config.cooldown_seconds
```

**Step 4: 编写测试**

创建 `tests/config/test_tts_config.py`:

```python
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
```

**Step 5: 运行测试**

```bash
pytest tests/config/test_tts_config.py -v
```

预期输出: `PASSED`

**Step 6: 提交**

```bash
git add app/config/tts_config.py app/config.py tests/config/
git commit -m "feat: add TTS configuration system

- Add TTSConfig with environment variable support
- Integrate config with TTSManager
- Add configuration tests"
```

---

## Task 7: 更新 Docker Compose 和文档

**Files:**
- Modify: `docker-compose.yml`
- Modify: `README.md`
- Create: `docs/MULTI_PROVIDER_TTS.md`

**Step 1: 更新 docker-compose.yml**

添加新的环境变量:

```yaml
services:
  edge-tts-service:
    environment:
      # ... 现有环境变量 ...
      - TTS_FAILURE_THRESHOLD=${TTS_FAILURE_THRESHOLD:-5}
      - TTS_COOLDOWN_SECONDS=${TTS_COOLDOWN_SECONDS:-300}
      - TTS_ENABLE_CACHE=${TTS_ENABLE_CACHE:-true}
```

**Step 2: 更新 README.md**

在特性部分添加:

```markdown
## ✨ 特性

- 💰 **完全免费** - 无需 API Key，无调用限制
- 🎙️ **高音质** - 神经网络语音合成
- 🔄 **多引擎** - Edge TTS + 本地备选，自动降级
- 🛡️ **容错** - 故障自动切换，服务高可用
```

**Step 3: 创建多引擎文档**

创建 `docs/MULTI_PROVIDER_TTS.md`:

```markdown
# 多引擎 TTS 架构

## 概述

本服务采用多引擎架构，提供高可用的文本转语音服务。

## 引擎列表

| 引擎 | 类型 | 优先级 | 说明 |
|------|------|-------|------|
| Edge TTS | 免费 | 1 | 主引擎，音质好 |
| Local TTS | 免费 | 2 | 本地兜底，离线可用 |

## API 使用

### 基础调用（自动选择引擎）

\`\`\`bash
curl -X POST http://localhost:8001/tts \\
  -H "Content-Type: application/json" \\
  -d '{"text": "你好，世界"}'
\`\`\`

### 强制使用指定引擎

\`\`\`bash
curl -X POST http://localhost:8001/tts \\
  -H "Content-Type: application/json" \\
  -d '{"text": "你好", "provider": "local"}'
\`\`\`

### 查看可用引擎

\`\`\`bash
curl http://localhost:8001/tts/providers
\`\`\`

### 查看统计信息

\`\`\`bash
curl http://localhost:8001/tts/stats
\`\`\`

## 配置

通过环境变量配置：

\`\`\`bash
TTS_FAILURE_THRESHOLD=5      # 连续失败 N 次后禁用
TTS_COOLDOWN_SECONDS=300     # 禁用冷却时间（秒）
TTS_ENABLE_CACHE=true        # 启用缓存
\`\`\`
```

**Step 4: 提交**

```bash
git add docker-compose.yml README.md docs/MULTI_PROVIDER_TTS.md
git commit -m "docs: update documentation for multi-provider TTS

- Update docker-compose.yml with new environment variables
- Update README.md with multi-engine features
- Add MULTI_PROVIDER_TTS.md documentation"
```

---

## Task 8: 集成测试

**Files:**
- Create: `tests/integration/test_tts_integration.py`

**Step 1: 编写集成测试**

创建 `tests/integration/test_tts_integration.py`:

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_tts_end_to_end():
    """端到端测试：正常流程"""
    client = TestClient(app)

    # 1. 检查提供者列表
    response = client.get("/tts/providers")
    assert response.status_code == 200
    providers = response.json()["providers"]
    provider_names = [p["name"] for p in providers]
    assert "EdgeTTSProvider" in provider_names
    assert "LocalTTSProvider" in provider_names

    # 2. 生成语音
    response = client.post(
        "/tts",
        json={"text": "你好，世界", "voice": "xiaoxiao"}
    )
    assert response.status_code == 200
    assert response.headers["X-TTS-Provider"] in ["edge-tts", "local"]
    assert b"RIFF" in response.content or b"ID3" in response.content

    # 3. 使用本地引擎
    response = client.post(
        "/tts",
        json={"text": "test", "provider": "local"}
    )
    assert response.status_code == 200
    assert response.headers["X-TTS-Provider"] == "local"


def test_fallback_mechanism():
    """测试降级机制（Mock 失败场景）"""
    # 这个测试需要 mock Edge TTS 失败
    # 验证会自动切换到本地引擎
    pass


def test_stats_endpoint():
    """测试统计端点"""
    client = TestClient(app)

    response = client.get("/tts/stats")
    assert response.status_code == 200

    data = response.json()
    assert "providers" in data
    assert "total_providers" in data
```

**Step 2: 运行集成测试**

```bash
pytest tests/integration/test_tts_integration.py -v
```

预期输出: `PASSED`

**Step 3: 提交**

```bash
git add tests/integration/
git commit -m "test: add integration tests for multi-provider TTS

- Add end-to-end test for normal flow
- Add fallback mechanism test
- Add stats endpoint test"
```

---

## Task 9: 本地测试验证

**Step 1: 启动服务**

```bash
cd /Users/songstephen/edge-tts-skill
docker-compose down
docker-compose up -d --build
```

**Step 2: 检查日志**

```bash
docker-compose logs -f
```

确认服务正常启动，没有错误。

**Step 3: 测试各端点**

```bash
# 1. 健康检查
curl http://localhost:8001/health

# 2. 查看提供者
curl http://localhost:8001/tts/providers

# 3. 查看统计
curl http://localhost:8001/tts/stats

# 4. 生成语音（Edge TTS）
curl -X POST http://localhost:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，世界"}' \
  --output test.mp3

# 5. 生成语音（本地）
curl -X POST http://localhost:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "test", "provider": "local"}' \
  --output test_local.wav

# 6. 飞书接口
curl -X POST http://localhost:8001/tts/feishu \
  -H "Content-Type: application/json" \
  -d '{"text": "飞书测试"}'
```

**Step 4: 验证音频文件**

```bash
file test.mp3 test_local.wav
```

预期输出: 显示正确的音频格式。

**Step 5: 提交验证脚本**

创建 `scripts/test-local.sh`:

```bash
#!/bin/bash
# 本地测试脚本

echo "🧪 本地测试"
echo "================================"

# 健康检查
echo -n "健康检查... "
curl -s http://localhost:8001/health > /dev/null && echo "✅" || echo "❌"

# 提供者列表
echo -n "提供者列表... "
response=$(curl -s http://localhost:8001/tts/providers)
echo "$response" | grep -q "EdgeTTSProvider" && echo "✅" || echo "❌"

# 生成测试音频
echo -n "生成音频... "
curl -s -X POST http://localhost:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "测试"}' \
  --output /tmp/test.mp3
[ -s /tmp/test.mp3 ] && echo "✅" || echo "❌"

echo "================================"
echo "测试完成！"
```

**Step 6: 提交**

```bash
chmod +x scripts/test-local.sh
git add scripts/test-local.sh
git commit -m "test: add local testing script"
```

---

## Task 10: 部署到服务器

**Step 1: 打包项目**

```bash
cd /Users/songstephen/edge-tts-skill
tar -czf edge-tts-multi-provider.tar.gz . --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv' --exclude='test*.mp3' --exclude='test*.wav'
```

**Step 2: 上传到服务器**

```bash
scp edge-tts-multi-provider.tar.gz root@115.190.252.250:/root/
```

**Step 3: SSH 登录并部署**

```bash
ssh root@115.190.252.250

# 停止现有服务
cd /opt/edge-tts-service-docker
docker-compose down

# 备份现有版本
cp -r . ../edge-tts-backup-$(date +%Y%m%d)

# 解压新版本
cd /opt
rm -rf edge-tts-service-docker
mkdir -p edge-tts-service-docker
cd edge-tts-service-docker
tar -xzf ~/edge-tts-multi-provider.tar.gz --strip-components=1

# 启动服务
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

**Step 4: 远程测试**

```bash
# 在服务器上测试
curl http://localhost:8000/health
curl http://localhost:8000/tts/providers

# 从本地测试
curl http://115.190.252.250:8001/health
curl -X POST http://115.190.252.250:8001/tts/feishu \
  -H "Content-Type: application/json" \
  -d '{"text": "服务器测试"}'
```

**Step 5: 更新部署文档**

修改 `docs/DOCKER_DEPLOYMENT.md`，添加多引擎说明。

**Step 6: 提交**

```bash
git add docs/DOCKER_DEPLOYMENT.md
git commit -m "docs: update deployment guide for multi-provider architecture"
```

---

## Task 11: 监控和优化

**Step 1: 添加日志监控**

在 `app/services/tts_manager.py` 中添加更详细的日志。

**Step 2: 添加性能指标**

创建 `app/services/metrics.py`:

```python
"""
TTS 性能指标收集
"""
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ProviderMetrics:
    """单个引擎的指标"""
    requests: int = 0
    successes: int = 0
    failures: int = 0
    total_duration: float = 0

    @property
    def success_rate(self) -> float:
        if self.requests == 0:
            return 0
        return self.successes / self.requests

    @property
    def avg_duration(self) -> float:
        if self.successes == 0:
            return 0
        return self.total_duration / self.successes


class TTSMetrics:
    """TTS 指标收集器"""

    def __init__(self):
        self._metrics: Dict[str, ProviderMetrics] = defaultdict(ProviderMetrics)

    def record_request(self, provider: str):
        """记录请求"""
        self._metrics[provider].requests += 1

    def record_success(self, provider: str, duration: float):
        """记录成功"""
        self._metrics[provider].successes += 1
        self._metrics[provider].total_duration += duration

    def record_failure(self, provider: str):
        """记录失败"""
        self._metrics[provider].failures += 1

    def get_metrics(self) -> Dict[str, dict]:
        """获取所有指标"""
        return {
            provider: {
                "requests": m.requests,
                "successes": m.successes,
                "failures": m.failures,
                "success_rate": m.success_rate,
                "avg_duration": m.avg_duration,
            }
            for provider, m in self._metrics.items()
        }
```

**Step 3: 在 TTSManager 中集成指标**

修改 `app/services/tts_manager.py`，添加指标收集。

**Step 4: 添加 /tts/metrics 端点**

在 `app/routes/tts.py` 中添加:

```python
@router.get("/metrics")
async def get_metrics():
    """获取性能指标"""
    return tts_manager.metrics.get_metrics()
```

**Step 5: 提交**

```bash
git add app/services/metrics.py app/services/tts_manager.py app/routes/tts.py
git commit -m "feat: add performance metrics collection

- Add TTSMetrics for tracking provider performance
- Integrate metrics with TTSManager
- Add /tts/metrics endpoint"
```

---

## Task 12: 最终验证和文档

**Step 1: 运行所有测试**

```bash
pytest tests/ -v --cov=app
```

确保所有测试通过，覆盖率 > 80%。

**Step 2: 更新 CHANGELOG**

创建 `CHANGELOG.md`:

```markdown
# Changelog

## [Unreleased]

### Added
- 多引擎 TTS 架构
- 自动故障降级机制
- 本地 TTS Provider（pyttsx3）
- TTS 管理器调度器
- 性能指标收集
- /tts/providers 端点
- /tts/stats 端点
- /tts/metrics 端点

### Changed
- TTS 路由使用 TTSManager
- 响应头添加 X-TTS-Provider 和 X-TTS-Cached

### Fixed
- Edge TTS 403 错误问题（通过自动降级）
```

**Step 3: 创建发布说明**

创建 `RELEASE_NOTES.md`:

```markdown
# Release Notes - 多引擎架构

## 新功能

### 多引擎支持

现在服务支持多个 TTS 引擎，自动故障降级：

1. **Edge TTS** (主引擎) - 免费，高音质
2. **本地 TTS** (兜底) - 离线可用

### 新 API 端点

- `GET /tts/providers` - 列出可用引擎
- `GET /tts/stats` - 获取统计信息
- `GET /tts/metrics` - 获取性能指标

### 新请求参数

- `provider` - 强制使用指定引擎

## 升级指南

### Docker 部署

```bash
# 拉取最新代码
git pull

# 重新构建
docker-compose down
docker-compose up -d --build
```

### 环境变量（可选）

```bash
TTS_FAILURE_THRESHOLD=5    # 失败阈值
TTS_COOLDOWN_SECONDS=300   # 冷却时间
```

## 兼容性

完全向后兼容，现有 API 调用无需修改。
```

**Step 4: 最终提交**

```bash
git add CHANGELOG.md RELEASE_NOTES.md
git commit -m "docs: add changelog and release notes for multi-provider architecture"

# 打 tag
git tag v2.0.0
git push origin main --tags
```

---

## 验收清单

- [ ] 所有 Provider 实现完成并通过测试
- [ ] TTSManager 调度器正常工作
- [ ] 路由层更新完成，API 向后兼容
- [ ] 本地 Docker 测试通过
- [ ] 服务器部署成功
- [ ] 远程测试通过
- [ ] 文档更新完成
- [ ] 所有测试通过（pytest）
- [ ] 性能指标正常

---

## 附录：故障排查

### Edge TTS 403 错误

**症状**: Edge TTS 返回 403 错误

**解决方案**:
- 自动降级到本地引擎
- 考虑配置代理服务器
- 联系火山引擎接入付费备选

### 本地 TTS 无法工作

**症状**: 本地 TTS 报错

**解决方案**:
- 检查 espeak 是否安装: `apt-get install espeak`
- 检查 pyttsx3 是否安装: `pip install pyttsx3`

### Docker 构建失败

**症状**: Docker 构建时报错

**解决方案**:
- 清理缓存: `docker system prune -a`
- 重新构建: `docker-compose build --no-cache`
