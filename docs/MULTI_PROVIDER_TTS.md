# 多引擎 TTS 架构

## 概述

本服务采用多引擎架构，提供高可用的文本转语音服务。

## 引擎列表

| 引擎 | 类型 | 优先级 | 说明 |
|------|------|-------|------|
| Edge TTS | 免费 | 1 | 主引擎，音质好 |
| Local TTS | 免费 | 2 | 本地兜底，离线可用 |

## API 使用

### 基础调用

```bash
curl -X POST http://localhost:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，世界"}'
```

### 强制使用本地引擎

```bash
curl -X POST http://localhost:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好", "provider": "local"}'
```

### 查看可用引擎

```bash
curl http://localhost:8001/tts/providers
```

### 查看统计信息

```bash
curl http://localhost:8001/tts/stats
```

## 配置

通过环境变量配置：

```bash
TTS_FAILURE_THRESHOLD=5    # 失败阈值
TTS_COOLDOWN_SECONDS=300   # 冷却时间（秒）
TTS_ENABLE_CACHE=true      # 启用缓存
```
