#!/bin/bash
# Opus 转换性能对比测试

echo "🧪 Opus 转换性能测试"
echo "================================"
echo ""

TTS_API="http://localhost:8000"

echo "测试参数:"
echo "  文本: '性能测试语音合成系统'"
echo "  音色: xiaoxiao"
echo "  次数: 10 次"
echo ""

echo "开始测试..."
echo ""

# 记录开始时间
START_TIME=$(date +%s)

# 测试 10 次
for i in {1..10}; do
    echo "测试 $i/10:"

    # 记录单次开始时间
    SINGLE_START=$(date +%s%N)

    # 发送请求
    RESULT=$(curl -s -X POST $TTS_API/tts/feishu \
      -H "Content-Type: application/json" \
      -d '{"text":"性能测试语音合成系统","voice":"xiaoxiao"}')

    # 记录结束时间
    SINGLE_END=$(date +%s%N)

    # 计算耗时（微秒）
    DURATION=$(( (SINGLE_END - SINGLE_START) / 1000 ))

    # 提取 duration 和 cached
    DURATION_MS=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('duration', 0))")
    CACHED=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('cached', False))")

    CACHE_STATUS="✅ 缓存" if [ "$CACHED" = "true" ]; then CACHE_STATUS="❌ 未缓存"; fi

    echo "  耗时: ${DURATION}ms | 报告: ${DURATION_MS}ms | $CACHE_STATUS"
    echo ""

    # 短暂延迟
    sleep 0.1
done

# 计算总耗时
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

echo "================================"
echo "测试完成！"
echo "总耗时: ${TOTAL_TIME}秒"
echo ""
echo "📊 性能统计:"
echo "  查看: curl $TTS_API/tts/performance"
