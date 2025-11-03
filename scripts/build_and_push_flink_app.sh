#!/bin/bash
#
# 构建并推送 Flink Application Mode 镜像到 ACR
#
# 执行位置：本地开发机器或 CI/CD 环境
#

set -e

echo "========================================"
echo "构建 Flink Application Mode 镜像"
echo "========================================"
echo ""

# 镜像信息
REGISTRY="registry.cn-beijing.aliyuncs.com"
NAMESPACE="lemo_zls"
IMAGE_NAME="flink-app"
TAG="latest"
FULL_IMAGE="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${TAG}"

# 1. 构建镜像
echo "步骤 1/3: 构建 Docker 镜像..."
echo "镜像名称: ${FULL_IMAGE}"
echo ""

docker build -f Dockerfile.flink-app -t ${FULL_IMAGE} .

echo ""
echo "✓ 镜像构建完成"
echo ""

# 2. 登录 ACR
echo "步骤 2/3: 登录阿里云容器镜像服务..."
echo "请输入 ACR 凭证（如已登录可跳过）"
echo ""

docker login --username=你的用户名 ${REGISTRY} || {
    echo "⚠️  登录失败，请检查凭证"
    exit 1
}

echo ""
echo "✓ 登录成功"
echo ""

# 3. 推送镜像
echo "步骤 3/3: 推送镜像到 ACR..."
echo ""

docker push ${FULL_IMAGE}

echo ""
echo "========================================"
echo "✓ 镜像构建并推送成功！"
echo "========================================"
echo ""
echo "镜像地址: ${FULL_IMAGE}"
echo ""
echo "下一步："
echo "  1. 在服务器2上执行: bash scripts/install_flink_operator.sh"
echo "  2. 更新 K8s 配置: kubectl apply -f k8s-deploy/k8s-deployment-http-grpc.yaml"
echo "  3. 重启服务: kubectl rollout restart deployment/lemo-service-recommender-http -n lemo-dev"
echo ""

