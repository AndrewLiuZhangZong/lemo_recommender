#!/bin/bash
# 测试 Docker 构建脚本
# 用于验证 Dockerfile 和新的服务入口点是否正常工作

set -e

echo "========================================="
echo "测试 Docker 构建"
echo "========================================="
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker daemon 未运行，请先启动 Docker"
    exit 1
fi

echo "[1/3] 检查项目结构..."
echo "  ✓ app/ 目录: $([ -d app ] && echo '存在' || echo '不存在')"
echo "  ✓ services/ 目录: $([ -d services ] && echo '存在' || echo '不存在')"
echo "  ✓ scripts/ 目录: $([ -d scripts ] && echo '存在' || echo '不存在')"
echo "  ✓ config/ 目录: $([ -d config ] && echo '存在' || echo '不存在')"
echo "  ✓ Dockerfile: $([ -f Dockerfile ] && echo '存在' || echo '不存在')"
echo ""

echo "[2/3] 检查服务入口点..."
ENTRY_POINTS=(
    "services/recommender/main_http.py"
    "services/recommender/main_grpc.py"
    "services/worker/main.py"
    "services/beat/main.py"
    "services/consumer/main.py"
)

for entry in "${ENTRY_POINTS[@]}"; do
    if [ -f "$entry" ]; then
        echo "  ✓ $entry"
    else
        echo "  ❌ $entry 不存在"
        exit 1
    fi
done
echo ""

echo "[3/3] 测试 Python 语法..."
python3 -m py_compile services/recommender/main_http.py \
    services/recommender/main_grpc.py \
    services/worker/main.py \
    services/beat/main.py \
    services/consumer/main.py 2>&1

if [ $? -eq 0 ]; then
    echo "  ✓ 所有 Python 文件语法正确"
else
    echo "  ❌ Python 文件语法错误"
    exit 1
fi
echo ""

echo "========================================="
echo "✅ 预检查通过！"
echo "========================================="
echo ""
echo "现在可以运行 Docker 构建："
echo "  docker build -t lemo-recommender:test ."
echo ""
echo "或者使用跨平台构建："
echo "  docker buildx build --platform linux/amd64 -t lemo-recommender:test --load ."
echo ""

