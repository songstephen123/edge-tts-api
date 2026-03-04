#!/bin/bash
# Edge TTS Service - cURL 使用示例

echo "=== Edge TTS Service cURL 示例 ==="
echo ""

# 配置
BASE_URL="http://localhost:8000"

echo "1. 健康检查"
echo " curl $BASE_URL/health"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""
echo ""

echo "2. 简单文本转语音"
echo " curl -X POST $BASE_URL/tts -d '{\"text\":\"你好，世界\"}' --output hello.mp3"
curl -X POST "$BASE_URL/tts" \
  -H "Content-Type: application/json" \
  -d '{"text":"你好，世界"}' \
  --output hello.mp3
echo "✅ 已保存到 hello.mp3"
echo ""
echo ""

echo "3. 指定音色 (xiaoxiao = 晓晓)"
echo " curl -X POST $BASE_URL/tts -d '{\"text\":\"你好，我是晓晓\",\"voice\":\"xiaoxiao\"}' --output xiaoxiao.mp3"
curl -X POST "$BASE_URL/tts" \
  -H "Content-Type: application/json" \
  -d '{"text":"你好，我是晓晓","voice":"xiaoxiao"}' \
  --output xiaoxiao.mp3
echo "✅ 已保存到 xiaoxiao.mp3"
echo ""
echo ""

echo "4. 调整语速和音调"
echo " curl -X POST $BASE_URL/tts -d '{\"text\":\"快速说话\",\"rate\":\"+20%\"}' --output fast.mp3"
curl -X POST "$BASE_URL/tts" \
  -H "Content-Type: application/json" \
  -d '{"text":"我说话很快","rate":"+20%"}' \
  --output fast.mp3
echo "✅ 已保存到 fast.mp3"
echo ""
echo ""

echo "5. 获取中文音色列表"
echo " curl $BASE_URL/voices/chinese"
curl -s "$BASE_URL/voices/chinese" | python3 -m json.tool
echo ""
echo ""

echo "6. 获取常用音色"
echo " curl $BASE_URL/voices/popular"
curl -s "$BASE_URL/voices/popular" | python3 -m json.tool
echo ""
echo ""

echo "完成！"
