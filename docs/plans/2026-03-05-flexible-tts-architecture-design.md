# 灵活 TTS 提供者架构设计文档

**日期**: 2026-03-05
**状态**: 已批准
**作者**: Claude + 用户

---

## 1. 概述

### 1.1 背景

当前 Edge TTS API 返回 403 错误，服务不可用。观察发现：
- 昨天同一服务器、同一网络环境可以正常使用
- 今天出现 403 错误，说明是 Microsoft 的主动封锁

### 1.2 设计目标

- 解决当前 403 错误问题
- 建立长期稳定的 TTS 服务架构
- 支持免费为主 + 付费备选的混合方案
- 本周内完成实现

### 1.3 核心策略

采用 **Provider 模式**，实现多个 TTS 引擎的统一管理和自动降级。

---

## 2. 架构设计

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
├─────────────────────────────────────────────────────────────┤
│                    TTS Manager (核心)                        │
│  - 引擎选择逻辑                                               │
│  - 失败重试/降级                                              │
│  - 缓存管理                                                   │
├─────────────────────────────────────────────────────────────┤
│              Provider Interface (统一接口)                   │
├──────────┬──────────┬──────────┬─────────────────────────────┤
│Edge TTS  │Volcengine│ 本地     │   未来扩展...                │
│ (免费)   │ (付费)   │pyttsx3   │                              │
└──────────┴──────────┴──────────┴─────────────────────────────┘
```

### 2.2 组件设计

#### 2.2.1 Provider 基类 (base.py)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class TTSResult:
    audio_data: bytes
    format: str  # mp3, opus, wav
    provider: str
    cached: bool = False

class TTSProvider(ABC):
    @abstractmethod
    async def text_to_speech(self, text: str, voice: str, ...) -> TTSResult: pass

    @abstractmethod
    async def get_available_voices(self) -> list[dict]: pass

    @property
    def is_free(self) -> bool: pass

    @property
    def priority(self) -> int: pass
```

#### 2.2.2 TTS Manager (tts_manager.py)

核心调度器，负责：
- 按优先级选择引擎
- 失败自动降级
- 缓存管理
- 失败统计和冷却机制

#### 2.2.3 具体 Provider 实现

| Provider | 类型 | 优先级 | 说明 |
|----------|------|-------|------|
| EdgeTTSProvider | 免费 | 1 | 主引擎，可能被封锁 |
| VolcengineTTSProvider | 付费 | 2 | 备选引擎 |
| LocalTTSProvider | 免费 | 3 | 本地离线兜底 |

---

## 3. 引擎方案

### 3.1 Edge TTS (免费)

- **优点**: 完全免费，音质好
- **缺点**: 可能被封锁，不稳定
- **用途**: 日常主引擎

### 3.2 火山引擎 (付费)

- **优点**: 稳定可靠，国内访问快
- **缺点**: 需要付费
- **用途**: 重要场景备选

### 3.3 本地 pyttsx3 (免费)

- **优点**: 完全离线，永远可用
- **缺点**: 音质一般
- **用途**: 紧急兜底

---

## 4. 故障处理机制

### 4.1 失败降级

```
Edge TTS 失败 → 尝试火山引擎 → 尝试本地 → 抛错
```

### 4.2 冷却机制

- 连续失败 N 次 → 暂时禁用该引擎
- 冷却时间后 → 重新尝试

### 4.3 缓存策略

- 复用现有 Opus 缓存
- 缓存命中直接返回，不调用任何引擎

---

## 5. API 兼容性

### 5.1 现有 API（不变）

```bash
POST /tts
POST /tts/feishu
POST /tts/url
```

### 5.2 新增参数（可选）

```json
{
  "provider": "volcengine"  // 强制使用指定引擎
}
```

### 5.3 新增端点

```
GET /tts/providers  # 列出可用引擎
GET /tts/stats      # 获取统计信息
```

---

## 6. 目录结构

```
app/
├── services/
│   ├── tts_manager.py           # 核心调度器
│   ├── tts_providers/           # 提供者目录
│   │   ├── __init__.py
│   │   ├── base.py              # 基类和接口
│   │   ├── edge_tts_provider.py # Edge TTS
│   │   ├── volcengine_provider.py # 火山引擎
│   │   └── local_provider.py    # 本地 TTS
│   └── tts_cache.py             # 缓存服务
├── routes/
│   └── tts.py                   # 更新的路由
└── config/
    └── tts_config.py            # TTS 配置
```

---

## 7. 部署计划

### 7.1 渐进式迁移

| 阶段 | 内容 |
|------|------|
| 阶段 1 | 保持现有服务运行 |
| 阶段 2 | 添加 Manager 层，Edge TTS 包装为 provider |
| 阶段 3 | 添加备选引擎（火山引擎、本地） |
| 阶段 4 | 监控和优化 |

### 7.2 环境变量

```bash
TTS_PRIMARY_PROVIDER=edge-tts
TTS_FALLBACK_PROVIDERS=volcengine,local
TTS_FAILURE_THRESHOLD=5
TTS_COOLDOWN_SECONDS=300
```

### 7.3 Docker 更新

添加 espeak 依赖（本地 TTS 需要）：
```dockerfile
RUN apt-get install -y espeak espeak-data libespeak1
RUN pip install pyttsx3
```

---

## 8. 回滚方案

```bash
git tag backup-before-refactor
git checkout backup-before-refactor
docker-compose down
docker-compose up -d --build
```

---

## 9. 时间估算

| 任务 | 预计时间 |
|------|---------|
| 创建 Provider 基类和接口 | 1 小时 |
| 实现 Edge TTS Provider | 30 分钟 |
| 实现 TTS Manager | 2 小时 |
| 更新路由层 | 1 小时 |
| 添加火山引擎 Provider | 2 小时 |
| 添加本地 Provider | 1 小时 |
| 测试和调试 | 2 小时 |
| 更新文档 | 30 分钟 |
| **总计** | **~10 小时** |

---

## 10. 验收标准

- [ ] Edge TTS 失败时自动切换到备选引擎
- [ ] 所有现有 API 继续正常工作
- [ ] 缓存机制继续有效
- [ ] 新增 `/tts/providers` 和 `/tts/stats` 端点
- [ ] Docker 部署成功
- [ ] 文档更新完成

---

## 附录

### A. 相关文档

- [Docker 部署指南](../DOCKER_DEPLOYMENT.md)
- [API 文档](../API.md)

### B. 参考资料

- edge-tts: https://github.com/rany2/edge-tts
- 火山引擎 TTS: https://www.volcengine.com/docs/category/TTS
- pyttsx3: https://pyttsx3.readthedocs.io/
