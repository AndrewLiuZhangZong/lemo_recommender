#!/bin/bash
# Flink Python 镜像构建和推送到 ACR 脚本
# 用途：构建包含 Python 支持的 Flink 镜像并推送到阿里云容器镜像服务

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
ACR_REGISTRY="${ACR_REGISTRY:-registry.cn-shenzhen.aliyuncs.com}"
ACR_NAMESPACE="${ACR_NAMESPACE:-lemo-ai}"
IMAGE_NAME="flink-python"
IMAGE_TAG="${IMAGE_TAG:-1.19}"
FULL_IMAGE="${ACR_REGISTRY}/${ACR_NAMESPACE}/${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Flink Python 镜像构建和推送脚本${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}配置信息:${NC}"
echo "  ACR 仓库: ${ACR_REGISTRY}"
echo "  命名空间: ${ACR_NAMESPACE}"
echo "  镜像名称: ${IMAGE_NAME}"
echo "  镜像标签: ${IMAGE_TAG}"
echo "  完整镜像: ${FULL_IMAGE}"
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker 运行正常${NC}"

# 检查 Dockerfile 是否存在
if [ ! -f "Dockerfile.flink-python" ]; then
    echo -e "${RED}✗ Dockerfile.flink-python 不存在${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Dockerfile.flink-python 存在${NC}"
echo ""

# 构建镜像
echo -e "${YELLOW}步骤 1: 构建镜像${NC}"
echo "----------------------------------------"
docker build \
    -f Dockerfile.flink-python \
    -t ${IMAGE_NAME}:${IMAGE_TAG} \
    -t ${IMAGE_NAME}:latest \
    -t ${FULL_IMAGE} \
    -t ${ACR_REGISTRY}/${ACR_NAMESPACE}/${IMAGE_NAME}:latest \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 镜像构建成功${NC}"
else
    echo -e "${RED}✗ 镜像构建失败${NC}"
    exit 1
fi
echo ""

# 登录 ACR
echo -e "${YELLOW}步骤 2: 登录 ACR${NC}"
echo "----------------------------------------"
echo "请输入 ACR 用户名（回车跳过自动登录）:"
read ACR_USERNAME

if [ -n "$ACR_USERNAME" ]; then
    echo "请输入 ACR 密码:"
    read -s ACR_PASSWORD
    echo ""
    
    echo "$ACR_PASSWORD" | docker login \
        --username "$ACR_USERNAME" \
        --password-stdin \
        "$ACR_REGISTRY"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ACR 登录成功${NC}"
    else
        echo -e "${RED}✗ ACR 登录失败${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}跳过登录（假设已登录）${NC}"
fi
echo ""

# 推送镜像
echo -e "${YELLOW}步骤 3: 推送镜像到 ACR${NC}"
echo "----------------------------------------"

# 推送带版本号的镜像
echo "推送: ${FULL_IMAGE}"
docker push ${FULL_IMAGE}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 推送成功: ${FULL_IMAGE}${NC}"
else
    echo -e "${RED}✗ 推送失败: ${FULL_IMAGE}${NC}"
    exit 1
fi

# 推送 latest 标签
LATEST_IMAGE="${ACR_REGISTRY}/${ACR_NAMESPACE}/${IMAGE_NAME}:latest"
echo "推送: ${LATEST_IMAGE}"
docker push ${LATEST_IMAGE}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 推送成功: ${LATEST_IMAGE}${NC}"
else
    echo -e "${RED}✗ 推送失败: ${LATEST_IMAGE}${NC}"
    exit 1
fi
echo ""

# 完成
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ 镜像构建和推送完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}镜像信息:${NC}"
echo "  - ${FULL_IMAGE}"
echo "  - ${LATEST_IMAGE}"
echo ""
echo -e "${YELLOW}使用方法:${NC}"
echo "  docker pull ${FULL_IMAGE}"
echo ""
echo -e "${YELLOW}更新 docker-compose.yml:${NC}"
echo "  flink:"
echo "    image: ${FULL_IMAGE}"
echo ""
echo -e "${YELLOW}更新 K8s Deployment:${NC}"
echo "  containers:"
echo "  - name: flink"
echo "    image: ${FULL_IMAGE}"
echo ""

