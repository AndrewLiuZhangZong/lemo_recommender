#!/bin/bash
set -e

# 配置项
ACR_REGISTRY="registry.cn-beijing.aliyuncs.com"
ACR_NAMESPACE="lemo_zls"
ACR_IMAGE="lemo-service-ranking"
ACR_TAG="$(date +%Y-%m-%d-%H-%M-%S)"
ACR_USERNAME="北京乐莫科技"
ACR_PASSWORD="Andrew1870361"
KUBECONFIG_FILE="$(pwd)/k8s-deploy/k3s-jd-config.yaml"
K8S_YAML="$(pwd)/k8s-deploy/k8s-deployment-ranking-service.yaml"
TMP_YAML="/tmp/k8s-ranking-service-apply.yaml"
NAMESPACE="lemo-dev"

IMAGE="$ACR_REGISTRY/$ACR_NAMESPACE/$ACR_IMAGE:$ACR_TAG"

echo "========================================="
echo "部署精排服务 (Ranking Service)"
echo "========================================="

# 1. 构建镜像
echo "[1/5] 构建Docker镜像（AMD64平台）..."
docker buildx build --platform linux/amd64 -t $IMAGE --load .

echo "[2/5] 登录阿里云ACR..."
docker login $ACR_REGISTRY -u "$ACR_USERNAME" -p "$ACR_PASSWORD"

echo "[3/5] 推送镜像到ACR..."
docker push $IMAGE

# 4. 删除原有Deployment
echo "[4/5] 删除原有Deployment（如存在）..."
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE delete deployment ranking-service || true

# 5. 应用K8s配置
echo "[5/5] 应用K8s部署文件..."
export IMAGE
envsubst < $K8S_YAML > $TMP_YAML
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f $TMP_YAML

echo ""
echo "✅ 精排服务部署完成！"
echo ""
echo "查看服务状态："
echo "  kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE get pods -l app=ranking-service"
echo ""
echo "查看服务日志："
echo "  kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE logs -f deployment/ranking-service"
echo ""
echo "测试服务："
echo "  kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE port-forward svc/ranking-service 8082:8082"
echo "  curl http://localhost:8082/health"
echo ""

# 删除临时文件
rm -f $TMP_YAML

