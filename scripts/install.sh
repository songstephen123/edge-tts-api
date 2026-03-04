#!/bin/bash
# Edge TTS Service 安装脚本

set -e

echo "🎙️ Edge TTS Service 安装脚本"
echo "================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python 版本: $PYTHON_VERSION"

# 创建虚拟环境（可选）
read -p "📦 是否创建虚拟环境？(推荐) [y/N]: " create_venv
if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境已创建"

    # 激活虚拟环境
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    echo "✅ 虚拟环境已激活"
fi

# 安装依赖
echo "📥 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ 安装完成！"
echo ""
echo "📝 下一步:"
echo "  1. (可选) 复制 .env.example 到 .env 并修改配置"
echo "  2. 运行 bash scripts/start.sh 启动服务"
echo "  3. 访问 http://localhost:8000/docs 查看 API 文档"
