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
  -d '{"text": "测试", "provider": "local"}' \
  --output /tmp/test_audio.mp3
[ -s /tmp/test_audio.mp3 ] && echo "✅" || echo "❌"

echo "================================"
echo "测试完成！"
