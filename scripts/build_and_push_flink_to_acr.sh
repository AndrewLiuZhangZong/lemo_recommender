#!/bin/bash
# Flink Python 镜像构建和推送到阿里云 ACR
# 参考：k8s-deploy/deploy-http-grpc-service.sh

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🐳 Flink Python 镜像构建和推送到阿里云 ACR${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 配置项（与推荐服务使用相同的 ACR）
ACR_REGISTRY="registry.cn-beijing.aliyuncs.com"
ACR_NAMESPACE="lemo_zls"
ACR_IMAGE="flink-python"  # Flink Python 镜像名
ACR_TAG="1.19"  # Flink 版本号
ACR_USERNAME="北京乐莫科技"
ACR_PASSWORD="Andrew1870361"

# 完整镜像名称
IMAGE="$ACR_REGISTRY/$ACR_NAMESPACE/$ACR_IMAGE:$ACR_TAG"
IMAGE_LATEST="$ACR_REGISTRY/$ACR_NAMESPACE/$ACR_IMAGE:latest"

echo -e "${BLUE}📋 配置信息:${NC}"
echo "  ACR 仓库: ${ACR_REGISTRY}"
echo "  命名空间: ${ACR_NAMESPACE}"
echo "  镜像名称: ${ACR_IMAGE}"
echo "  镜像标签: ${ACR_TAG}"
echo "  完整镜像: ${IMAGE}"
echo ""

# 检查 Dockerfile 是否存在
if [ ! -f "Dockerfile.flink-python" ]; then
    echo -e "${RED}✗ 错误: Dockerfile.flink-python 不存在${NC}"
    echo "  请确保在项目根目录执行此脚本"
    exit 1
fi

# 1. 构建镜像（跨平台构建 AMD64，适配服务器）
echo -e "${YELLOW}[1/5] 构建 Docker 镜像（AMD64 平台）...${NC}"
echo "----------------------------------------"
docker buildx build --platform linux/amd64 \
    -f Dockerfile.flink-python \
    -t $IMAGE \
    -t $IMAGE_LATEST \
    --load \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 镜像构建成功${NC}"
else
    echo -e "${RED}✗ 镜像构建失败${NC}"
    exit 1
fi
echo ""

# 2. 登录阿里云 ACR
echo -e "${YELLOW}[2/5] 登录阿里云 ACR...${NC}"
echo "----------------------------------------"
docker login $ACR_REGISTRY -u "$ACR_USERNAME" -p "$ACR_PASSWORD"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ACR 登录成功${NC}"
else
    echo -e "${RED}✗ ACR 登录失败${NC}"
    exit 1
fi
echo ""

# 3. 推送镜像（推送两个标签：版本号 + latest）
echo -e "${YELLOW}[3/5] 推送镜像到 ACR...${NC}"
echo "----------------------------------------"

echo "推送: ${IMAGE}"
docker push $IMAGE

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 推送成功: ${IMAGE}${NC}"
else
    echo -e "${RED}✗ 推送失败: ${IMAGE}${NC}"
    exit 1
fi

echo "推送: ${IMAGE_LATEST}"
docker push $IMAGE_LATEST

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 推送成功: ${IMAGE_LATEST}${NC}"
else
    echo -e "${RED}✗ 推送失败: ${IMAGE_LATEST}${NC}"
    exit 1
fi
echo ""

# 4. 显示镜像信息
echo -e "${YELLOW}[4/5] 验证镜像信息...${NC}"
echo "----------------------------------------"
docker images | grep -E "flink-python|REPOSITORY"
echo ""

# 5. 完成
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 镜像构建和推送完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${BLUE}📦 已推送的镜像:${NC}"
echo "  ✓ ${IMAGE}"
echo "  ✓ ${IMAGE_LATEST}"
echo ""

echo -e "${BLUE}🚀 在服务器上使用:${NC}"
echo ""
echo "1️⃣ 拉取镜像:"
echo "   docker pull ${IMAGE}"
echo ""
echo "2️⃣ docker-compose.yml 配置:"
echo "   flink:"
echo "     image: ${IMAGE}"
echo ""
echo "3️⃣ 启动服务:"
echo "   docker-compose up -d flink flink-sql-gateway"
echo ""
echo "4️⃣ 验证:"
echo "   docker ps | grep flink"
echo "   curl http://localhost:8081/overview      # Flink UI"
echo "   curl http://localhost:8083/v1/info       # SQL Gateway"
echo ""

echo -e "${YELLOW}💡 提示:${NC}"
echo "  - Flink UI: http://服务器IP:8081"
echo "  - SQL Gateway: http://服务器IP:8083"
echo "  - 支持 JAR 和 Python 作业"
echo "  - 预装常用 Python 库"
echo ""

