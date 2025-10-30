#!/bin/bash
set -e

# 配置项（请根据实际情况修改）
ACR_REGISTRY="registry.cn-beijing.aliyuncs.com"
ACR_NAMESPACE="lemo_zls"
ACR_IMAGE="lemo-service-recommender"
ACR_TAG="$(date +%Y-%m-%d-%H-%M-%S)"
ACR_USERNAME="北京乐莫科技"
ACR_PASSWORD="Andrew1870361"
KUBECONFIG_FILE="$(pwd)/k8s-deploy/k3s-jd-config.yaml"
NAMESPACE="lemo-dev"

IMAGE="$ACR_REGISTRY/$ACR_NAMESPACE/$ACR_IMAGE:$ACR_TAG"

echo "========================================="
echo "部署所有推荐系统服务"
echo "========================================="
echo "服务清单："
echo "  1. HTTP API 服务 (10071)"
echo "  2. gRPC 服务 (10072)"
echo "  3. Celery Worker 服务 (×2)"
echo "  4. Celery Beat 服务 (×1)"
echo "  5. Kafka Consumer 服务"
echo "========================================="
echo ""

# 1. 构建镜像（跨平台构建 AMD64）
echo "[1/6] 本地构建 Docker 镜像（AMD64 平台）..."
docker buildx build --platform linux/amd64 -t $IMAGE --load .

echo "[2/6] 登录阿里云ACR..."
docker login $ACR_REGISTRY -u "$ACR_USERNAME" -p "$ACR_PASSWORD"

echo "[3/6] 推送镜像到ACR..."
docker push $IMAGE

# 4. 删除原有 Services（避免端口冲突）
echo "[4/6] 删除原有 Services（如存在）..."
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE delete svc lemo-service-recommender || true
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE delete svc lemo-service-recommender-grpc || true

# 5. 部署所有服务
echo "[5/6] 部署所有服务..."
export IMAGE

# 部署 HTTP + gRPC
echo "  → 部署 HTTP API + gRPC 服务..."
K8S_YAML="$(pwd)/k8s-deploy/k8s-deployment.yaml"
TMP_YAML="/tmp/k8s-recommender-core-apply.yaml"
envsubst < $K8S_YAML > $TMP_YAML
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f $TMP_YAML
rm -f $TMP_YAML

# 部署 Worker
echo "  → 部署 Celery Worker 服务..."
K8S_YAML="$(pwd)/k8s-deploy/k8s-deployment-worker.yaml"
TMP_YAML="/tmp/k8s-recommender-worker-apply.yaml"
envsubst < $K8S_YAML > $TMP_YAML
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f $TMP_YAML
rm -f $TMP_YAML

# 部署 Beat
echo "  → 部署 Celery Beat 服务..."
K8S_YAML="$(pwd)/k8s-deploy/k8s-deployment-beat.yaml"
TMP_YAML="/tmp/k8s-recommender-beat-apply.yaml"
envsubst < $K8S_YAML > $TMP_YAML
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f $TMP_YAML
rm -f $TMP_YAML

# 部署 Consumer
echo "  → 部署 Kafka Consumer 服务..."
K8S_YAML="$(pwd)/k8s-deploy/k8s-deployment-consumer.yaml"
TMP_YAML="/tmp/k8s-recommender-consumer-apply.yaml"
envsubst < $K8S_YAML > $TMP_YAML
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f $TMP_YAML
rm -f $TMP_YAML

# 6. 等待所有 Pod 就绪
echo "[6/6] 等待所有 Pod 就绪..."
echo "  → 等待 HTTP API..."
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE wait --for=condition=ready pod -l component=http --timeout=120s || true

echo "  → 等待 gRPC..."
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE wait --for=condition=ready pod -l component=grpc --timeout=120s || true

echo "  → 等待 Worker..."
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE wait --for=condition=ready pod -l component=worker --timeout=120s || true

echo "  → 等待 Beat..."
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE wait --for=condition=ready pod -l component=beat --timeout=120s || true

echo "  → 等待 Consumer..."
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE wait --for=condition=ready pod -l component=consumer --timeout=120s || true

echo ""
echo "========================================="
echo "✅ 所有服务部署完成！"
echo "========================================="
echo ""
echo "查看所有服务状态："
echo "  kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE get pods -l app=lemo-service-recommender"
echo ""
echo "查看服务详情："
echo "  kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE get svc -l app=lemo-service-recommender"
echo ""
echo "查看各服务日志："
echo "  HTTP API:      kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE logs -f deployment/lemo-service-recommender-http"
echo "  gRPC:          kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE logs -f deployment/lemo-service-recommender-grpc"
echo "  Worker:        kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE logs -f deployment/lemo-service-recommender-worker"
echo "  Beat:          kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE logs -f deployment/lemo-service-recommender-beat"
echo "  Consumer:      kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE logs -f deployment/lemo-service-recommender-consumer"
echo ""
echo "HTTP API 访问地址："
echo "  http://<K3S_NODE_IP>:30801/api/v1/docs"
echo ""

