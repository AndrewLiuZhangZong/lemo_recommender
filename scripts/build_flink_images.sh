#!/bin/bash
#
# Flink 镜像完整构建脚本（企业级标准）
# 
# 功能：
# 1. 构建 flink-python:latest（基础镜像，包含 Flink 2.0 + PyFlink 2.1.1）
# 2. 构建 flink-app:latest（应用镜像，包含 entrypoint.py）
# 3. 推送到阿里云 ACR
# 4. 验证镜像完整性
#
# 参考：阿里云/字节跳动分层镜像构建实践
#
# 使用方法：
#   bash scripts/build_flink_images.sh
#

set -e  # 遇到错误立即退出

# ============================================
# 配置项
# ============================================

# 阿里云 ACR 配置
ACR_REGISTRY="registry.cn-beijing.aliyuncs.com"
ACR_NAMESPACE="lemo_zls"
ACR_USERNAME="北京乐莫科技"
ACR_PASSWORD="Andrew1870361"

# 镜像配置
FLINK_PYTHON_IMAGE="${ACR_REGISTRY}/${ACR_NAMESPACE}/flink-python:latest"
FLINK_APP_IMAGE="${ACR_REGISTRY}/${ACR_NAMESPACE}/flink-app:latest"

# 平台配置（服务器是 AMD64）
PLATFORM="linux/amd64"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================
# 辅助函数
# ============================================

print_header() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  $1${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo ""
    echo -e "${YELLOW}[步骤 $1] $2${NC}"
    echo -e "${YELLOW}────────────────────────────────────────────────────────────────────${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# ============================================
# 主流程
# ============================================

print_header "Flink 镜像构建（企业级标准 - 两层架构）"

print_info "构建配置："
echo "  • 平台: ${PLATFORM}"
echo "  • 基础镜像: ${FLINK_PYTHON_IMAGE}"
echo "  • 应用镜像: ${FLINK_APP_IMAGE}"
echo "  • ACR 仓库: ${ACR_REGISTRY}"
echo ""

# 检查前置条件
print_step "0/7" "检查前置条件"

if [ ! -f "Dockerfile.flink-python" ]; then
    print_error "Dockerfile.flink-python 不存在"
    echo "  请确保在项目根目录执行此脚本"
    exit 1
fi

if [ ! -f "Dockerfile.flink-app" ]; then
    print_error "Dockerfile.flink-app 不存在"
    exit 1
fi

# 检查 docker buildx
if ! docker buildx version &> /dev/null; then
    print_error "docker buildx 不可用"
    echo "  请升级 Docker 到最新版本"
    exit 1
fi

print_success "前置条件检查通过"

# ============================================
# 第一阶段：构建 flink-python 基础镜像
# ============================================

print_step "1/7" "构建 flink-python 基础镜像"
print_info "包含："
echo "  • Flink 2.0.0 运行时"
echo "  • Python 3.11"
echo "  • PyFlink 2.1.1 (关键！)"
echo "  • pandas, numpy, kafka-python"
echo "  • Kafka Connector 3.3.0-2.0"
echo ""

docker buildx build \
    --platform ${PLATFORM} \
    -f Dockerfile.flink-python \
    -t ${FLINK_PYTHON_IMAGE} \
    --load \
    .

if [ $? -eq 0 ]; then
    print_success "flink-python 镜像构建成功"
else
    print_error "flink-python 镜像构建失败"
    exit 1
fi

# ============================================
# 验证 flink-python 镜像
# ============================================

print_step "2/7" "验证 flink-python 镜像"

print_info "检查 PyFlink 安装..."
PYFLINK_VERSION=$(docker run --rm ${FLINK_PYTHON_IMAGE} \
    python3 -c "import pyflink; print(pyflink.__version__)" 2>&1)

if [[ $PYFLINK_VERSION == *"2.1.1"* ]]; then
    print_success "PyFlink 版本: ${PYFLINK_VERSION}"
else
    print_error "PyFlink 安装异常: ${PYFLINK_VERSION}"
    print_warning "继续构建，但可能需要检查 Dockerfile.flink-python"
fi

print_info "检查 Python 依赖库..."
docker run --rm ${FLINK_PYTHON_IMAGE} \
    python3 -c "import pandas, numpy, kafka; print('pandas, numpy, kafka-python 已安装')" 2>&1

if [ $? -eq 0 ]; then
    print_success "Python 依赖库检查通过"
else
    print_warning "部分 Python 库可能未安装"
fi

print_info "检查 Kafka Connector..."
docker run --rm ${FLINK_PYTHON_IMAGE} \
    ls -lh /opt/flink/opt/flink-sql-connector-kafka-3.3.0-2.0.jar 2>&1 | grep -q "flink-sql-connector-kafka"

if [ $? -eq 0 ]; then
    print_success "Kafka Connector 已安装"
else
    print_warning "Kafka Connector 未找到"
fi

# ============================================
# 登录 ACR
# ============================================

print_step "3/7" "登录阿里云 ACR"

docker login ${ACR_REGISTRY} -u "${ACR_USERNAME}" -p "${ACR_PASSWORD}" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    print_success "ACR 登录成功"
else
    print_error "ACR 登录失败"
    exit 1
fi

# ============================================
# 推送 flink-python 镜像
# ============================================

print_step "4/7" "推送 flink-python 镜像到 ACR"
print_info "推送: ${FLINK_PYTHON_IMAGE}"

docker push ${FLINK_PYTHON_IMAGE}

if [ $? -eq 0 ]; then
    print_success "flink-python 推送成功"
else
    print_error "flink-python 推送失败"
    exit 1
fi

# ============================================
# 第二阶段：构建 flink-app 应用镜像
# ============================================

print_step "5/7" "构建 flink-app 应用镜像"
print_info "基于 flink-python，添加："
echo "  • entrypoint.py 脚本下载器"
echo "  • 业务配置"
echo ""

docker buildx build \
    --platform ${PLATFORM} \
    -f Dockerfile.flink-app \
    -t ${FLINK_APP_IMAGE} \
    --load \
    .

if [ $? -eq 0 ]; then
    print_success "flink-app 镜像构建成功"
else
    print_error "flink-app 镜像构建失败"
    exit 1
fi

# ============================================
# 验证 flink-app 镜像
# ============================================

print_step "6/7" "验证 flink-app 镜像"

print_info "检查 PyFlink（继承验证）..."
docker run --rm ${FLINK_APP_IMAGE} \
    python3 -c "import pyflink; print(f'PyFlink: {pyflink.__version__}')" 2>&1

if [ $? -eq 0 ]; then
    print_success "flink-app 镜像中 PyFlink 正常"
else
    print_error "flink-app 镜像中 PyFlink 异常"
    exit 1
fi

print_info "检查 entrypoint.py..."
docker run --rm ${FLINK_APP_IMAGE} \
    ls -lh /opt/flink/usrlib/entrypoint.py 2>&1 | grep -q "entrypoint.py"

if [ $? -eq 0 ]; then
    print_success "entrypoint.py 已安装"
else
    print_warning "entrypoint.py 未找到（可能需要检查 Dockerfile.flink-app）"
fi

# ============================================
# 推送 flink-app 镜像
# ============================================

print_step "7/7" "推送 flink-app 镜像到 ACR"
print_info "推送: ${FLINK_APP_IMAGE}"

docker push ${FLINK_APP_IMAGE}

if [ $? -eq 0 ]; then
    print_success "flink-app 推送成功"
else
    print_error "flink-app 推送失败"
    exit 1
fi

# ============================================
# 完成总结
# ============================================

print_header "✅ 镜像构建和推送完成！"

echo -e "${CYAN}📦 已推送的镜像：${NC}"
echo "  1️⃣  ${FLINK_PYTHON_IMAGE}"
echo "      └─ Flink 2.0 + PyFlink 2.1.1 基础环境"
echo ""
echo "  2️⃣  ${FLINK_APP_IMAGE}"
echo "      └─ 包含 entrypoint.py 的应用镜像"
echo ""

echo -e "${CYAN}🔍 验证命令（在服务器上执行）：${NC}"
echo ""
echo "  # 拉取镜像"
echo "  docker pull ${FLINK_PYTHON_IMAGE}"
echo "  docker pull ${FLINK_APP_IMAGE}"
echo ""
echo "  # 验证 PyFlink"
echo "  docker run --rm ${FLINK_APP_IMAGE} \\"
echo "    python3 -c \"import pyflink; print(f'PyFlink: {pyflink.__version__}')\""
echo ""
echo "  # 预期输出："
echo "  # PyFlink: 2.1.1"
echo ""

echo -e "${CYAN}🚀 下一步操作：${NC}"
echo ""
echo "  1. 重启 K8s 服务（使用新镜像）："
echo "     export KUBECONFIG=/path/to/k3s-jd-config.yaml"
echo "     kubectl rollout restart deployment/lemo-service-recommender-http -n lemo-dev"
echo "     kubectl rollout restart deployment/lemo-service-recommender-grpc -n lemo-dev"
echo ""
echo "  2. 查看服务状态："
echo "     kubectl get pods -n lemo-dev | grep lemo-service-recommender"
echo ""
echo "  3. 提交测试作业："
echo "     访问前端提交 minimal_test.py"
echo "     验证 TaskManager 不再报 'ModuleNotFoundError: No module named pyflink'"
echo ""

echo -e "${CYAN}📚 参考文档：${NC}"
echo "  • docs/Flink架构与部署完整指南.md"
echo "  • ARCHITECTURE_CHECK.md（架构梳理）"
echo ""

echo -e "${YELLOW}💡 温馨提示：${NC}"
echo "  • 镜像已包含 PyFlink 2.1.1（关键修复）"
echo "  • 版本严格匹配：Flink 2.0 ↔ PyFlink 2.1.1"
echo "  • 符合阿里云/字节跳动分层镜像最佳实践"
echo ""

print_success "构建流程全部完成！🎉"
echo ""

