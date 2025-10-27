#!/bin/bash
# 使用 protobuf 5.x 重新生成 gRPC 代码
# 确保与 TensorFlow 2.15 兼容

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 使用 Protobuf 5.x 重新生成 gRPC 代码"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 项目根目录
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_ROOT"

# Proto 源文件目录
PROTO_SOURCE="/Users/edy/Lemo/andrew-protos/protos"
OUTPUT_DIR="app/grpc_generated/python"

# 检查 proto 源目录
if [ ! -d "$PROTO_SOURCE" ]; then
    echo "❌ Proto 源目录不存在: $PROTO_SOURCE"
    exit 1
fi

# 1. 安装依赖（如果需要）
echo "[1/5] 检查依赖..."
if ! python3 -c "import grpc_tools" 2>/dev/null; then
    echo "  安装 grpcio-tools..."
    pip3 install grpcio==1.68.0 grpcio-tools==1.68.0 protobuf==5.29.0
else
    echo "  ✓ grpcio-tools 已安装"
fi

# 2. 清理旧文件
echo "[2/5] 清理旧的生成文件..."
rm -rf "$OUTPUT_DIR/common" "$OUTPUT_DIR/recommender"
mkdir -p "$OUTPUT_DIR"

# 3. 生成 Python 代码
echo "[3/5] 生成 Python 代码..."
python3 -m grpc_tools.protoc \
  -I="$PROTO_SOURCE" \
  --python_out="$OUTPUT_DIR" \
  --pyi_out="$OUTPUT_DIR" \
  --grpc_python_out="$OUTPUT_DIR" \
  "$PROTO_SOURCE"/common/v1/*.proto \
  "$PROTO_SOURCE"/recommender/v1/*.proto

# 4. 创建 __init__.py 文件
echo "[4/5] 创建 __init__.py 文件..."

# 为所有目录创建 __init__.py
find "$OUTPUT_DIR" -type d -exec touch {}/__init__.py \;

# 创建 lemo 包结构
mkdir -p "$OUTPUT_DIR/lemo/common/v1"
mkdir -p "$OUTPUT_DIR/lemo/recommender/v1"

# 创建 __init__.py
touch "$OUTPUT_DIR/lemo/__init__.py"
touch "$OUTPUT_DIR/lemo/common/__init__.py"
touch "$OUTPUT_DIR/lemo/common/v1/__init__.py"
touch "$OUTPUT_DIR/lemo/recommender/__init__.py"
touch "$OUTPUT_DIR/lemo/recommender/v1/__init__.py"

# 5. 验证生成的代码
echo "[5/5] 验证生成的代码..."
echo ""
echo "生成的文件列表："
find "$OUTPUT_DIR" -name "*_pb2.py" -o -name "*_pb2_grpc.py" | sort

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 代码生成完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 验证 protobuf 版本："
python3 -c "
import google.protobuf
print(f'  Protobuf 版本: {google.protobuf.__version__}')
"

echo ""
echo "🔍 检查生成的代码版本标识："
head -5 "$OUTPUT_DIR/recommender/v1/scenario_pb2.py" | grep "Protobuf Python Version"

echo ""
echo "🚀 现在可以重新构建 Docker 镜像了！"

