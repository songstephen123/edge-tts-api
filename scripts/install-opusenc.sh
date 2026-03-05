#!/bin/bash
# 安装 opusenc - 快速 Opus 编码器

echo "📦 安装 opusenc..."

# 检查是否已安装
if command -v opusenc &> /dev/null; then
    echo "✅ opusenc 已安装"
    opusenc --version
    exit 0
fi

# 更新包列表
apt update

# 安装 opus-tools
apt install -y opus-tools

# 验证安装
if command -v opusenc &> /dev/null; then
    echo "✅ opusenc 安装成功"
    opusenc --version
else
    echo "❌ opusenc 安装失败"
    exit 1
fi

echo ""
echo "📊 编码器对比:"
echo "  FFmpeg + libopus: 标准方案"
echo "  opusenc: 专业 Opus 编码器（更快 2-3x）"
