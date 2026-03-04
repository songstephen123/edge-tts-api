# Edge TTS API Skill

> 🎙️ 一个基于微软 Edge TTS 的完全免费的文本转语音 API 服务

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## ✨ 特性

- 💰 **完全免费** - 无需 API Key，无调用限制
- 🎙️ **高音质** - 神经网络语音合成
- 🌏 **多语言** - 支持 40+ 种语言和音色
- ⚡ **简单易用** - RESTful API，自动文档
- 🐳 **容器化** - Docker 一键部署
- 🔌 **易集成** - 可接入飞书、钉钉等

## 🚀 快速开始

### 通过 npx skills 安装（推荐）

```bash
npx skills add songstephen/edge-tts-api
cd ~/skills/edge-tts-api
bash scripts/start.sh
```

### 手动安装

```bash
git clone https://github.com/songstephen/edge-tts-api.git
cd edge-tts-api
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker 部署

```bash
docker-compose up -d
```

## 📖 使用示例

```bash
# 生成语音
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，世界"}' \
  --output hello.mp3

# 查看可用音色
curl http://localhost:8000/voices/popular

# 健康检查
curl http://localhost:8000/health
```

## 🎭 可用音色

| 简称 | 完整 ID | 性别 | 说明 |
|------|---------|------|------|
| `xiaoxiao` | zh-CN-XiaoxiaoNeural | 女 | 温柔女声（默认） |
| `yunyang` | zh-CN-YunyangNeural | 男 | 成熟男声 |
| `aria` | en-US-AriaNeural | 女 | 英文女声 |

## 📚 文档

- [API 文档](docs/API.md)
- [部署指南](docs/DEPLOYMENT.md)
- [火山引擎部署](docs/VOLCENGINE_DEPLOYMENT.md)
- [集成指南](docs/INTEGRATION.md)

## 🌐 访问地址

启动后访问：
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📝 License

[MIT](LICENSE)

## 🙏 致谢

- [edge-tts](https://github.com/rany2/edge-tts) - Edge TTS 核心库
- [NoizAI/skills](https://github.com/NoizAI/skills) - Skills 框架灵感
