#!/bin/bash
set -e

# 配置项（请根据实际情况修改）
ACR_REGISTRY="registry.cn-beijing.aliyuncs.com"
ACR_NAMESPACE="lemo_zls"
ACR_IMAGE="lemo-service-recommender-consumer"
ACR_TAG="$(date +%Y-%m-%d-%H-%M-%S)"
ACR_USERNAME="北京乐莫科技"
ACR_PASSWORD="Andrew1870361"
KUBECONFIG_FILE="$(pwd)/k8s-deploy/k3s-jd-config.yaml"
K8S_YAML="$(pwd)/k8s-deploy/k8s-deployment-consumer.yaml"
TMP_YAML="/tmp/k8s-recommender-consumer-apply.yaml"
NAMESPACE="lemo-dev"

IMAGE="$ACR_REGISTRY/$ACR_NAMESPACE/$ACR_IMAGE:$ACR_TAG"

echo "========================================="
echo "部署 Kafka Consumer 服务"
echo "========================================="

# 1. 构建镜像（跨平台构建 AMD64）
echo "[1/5] 本地构建 Docker 镜像（AMD64 平台）..."
docker buildx build --platform linux/amd64 -t $IMAGE --load .

echo "[2/5] 登录阿里云ACR..."
docker login $ACR_REGISTRY -u "$ACR_USERNAME" -p "$ACR_PASSWORD"

echo "[3/5] 推送镜像到ACR..."
docker push $IMAGE

# 4. 删除原有 Deployment（如果存在）
echo "[4/5] 删除原有 Consumer Deployment（如存在）..."
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE delete deployment lemo-service-recommender-consumer || true

# 5. 用envsubst替换镜像变量，apply到K3s
echo "[5/5] 应用 Consumer K8S部署文件..."
export IMAGE
envsubst < $K8S_YAML > $TMP_YAML
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f $TMP_YAML

echo ""
echo "✅ Kafka Consumer 服务部署完成！"
echo ""
echo "查看 Consumer 状态："
echo "  kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE get pods -l app=lemo-service-recommender-consumer"
echo ""
echo "查看 Consumer 日志："
echo "  kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE logs -f deployment/lemo-service-recommender-consumer"
echo ""
echo "查看 Kafka 消费进度："
echo "  kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE exec -it deployment/lemo-service-recommender-consumer -- python3 -c 'from app.core.kafka import KafkaConsumer; print(\"Consumer running\")'"
echo ""

# 删除临时文件
rm -f $TMP_YAML

