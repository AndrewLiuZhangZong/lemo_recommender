#!/bin/bash
set -e

# 配置项（请根据实际情况修改）
ACR_REGISTRY="registry.cn-beijing.aliyuncs.com"
ACR_NAMESPACE="lemo_zls"
ACR_BASE_IMAGE="lemo-service-recommender"
ACR_TAG="$(date +%Y-%m-%d-%H-%M-%S)"
ACR_USERNAME="北京乐莫科技"
ACR_PASSWORD="Andrew1870361"
KUBECONFIG_FILE="$(pwd)/k8s-deploy/k3s-jd-config.yaml"
NAMESPACE="lemo-dev"

# 基础镜像（所有服务共用）
BASE_IMAGE="$ACR_REGISTRY/$ACR_NAMESPACE/$ACR_BASE_IMAGE:$ACR_TAG"

# 各服务镜像名
HTTP_IMAGE="$ACR_REGISTRY/$ACR_NAMESPACE/lemo-service-recommender-http:$ACR_TAG"
GRPC_IMAGE="$ACR_REGISTRY/$ACR_NAMESPACE/lemo-service-recommender-grpc:$ACR_TAG"
WORKER_IMAGE="$ACR_REGISTRY/$ACR_NAMESPACE/lemo-service-recommender-worker:$ACR_TAG"
BEAT_IMAGE="$ACR_REGISTRY/$ACR_NAMESPACE/lemo-service-recommender-beat:$ACR_TAG"
CONSUMER_IMAGE="$ACR_REGISTRY/$ACR_NAMESPACE/lemo-service-recommender-consumer:$ACR_TAG"

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
echo "镜像标签: $ACR_TAG"
echo "========================================="
echo ""

# 1. 构建基础镜像（跨平台构建 AMD64）
echo "[1/6] 本地构建 Docker 镜像（AMD64 平台）..."
docker buildx build --platform linux/amd64 -t $BASE_IMAGE --load .

# 为每个服务打标签
echo "为各服务打标签..."
docker tag $BASE_IMAGE $HTTP_IMAGE
docker tag $BASE_IMAGE $GRPC_IMAGE
docker tag $BASE_IMAGE $WORKER_IMAGE
docker tag $BASE_IMAGE $BEAT_IMAGE
docker tag $BASE_IMAGE $CONSUMER_IMAGE

echo "[2/6] 登录阿里云ACR..."
docker login $ACR_REGISTRY -u "$ACR_USERNAME" -p "$ACR_PASSWORD"

echo "[3/6] 推送镜像到ACR..."
echo "  → 推送 HTTP 镜像..."
docker push $HTTP_IMAGE
echo "  → 推送 gRPC 镜像..."
docker push $GRPC_IMAGE
echo "  → 推送 Worker 镜像..."
docker push $WORKER_IMAGE
echo "  → 推送 Beat 镜像..."
docker push $BEAT_IMAGE
echo "  → 推送 Consumer 镜像..."
docker push $CONSUMER_IMAGE

# 4. 删除原有 Services（避免端口冲突）
echo "[4/6] 删除原有 Services（如存在）..."
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE delete svc lemo-service-recommender || true
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE delete svc lemo-service-recommender-grpc || true

# 5. 部署所有服务
echo "[5/6] 部署所有服务..."

# 部署 HTTP + gRPC
echo "  → 部署 HTTP API + gRPC 服务..."
export IMAGE=$HTTP_IMAGE
K8S_YAML="$(pwd)/k8s-deploy/k8s-deployment-http-grpc.yaml"
TMP_YAML="/tmp/k8s-recommender-http-apply.yaml"
envsubst < $K8S_YAML > $TMP_YAML

# 修改 gRPC 镜像
export IMAGE=$GRPC_IMAGE
sed -i.bak "s|recommender-grpc.*image:.*|recommender-grpc\n        image: $GRPC_IMAGE|" $TMP_YAML
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f $TMP_YAML
rm -f $TMP_YAML $TMP_YAML.bak

# 部署 Worker
echo "  → 部署 Celery Worker 服务..."
export IMAGE=$WORKER_IMAGE
K8S_YAML="$(pwd)/k8s-deploy/k8s-deployment-worker.yaml"
TMP_YAML="/tmp/k8s-recommender-worker-apply.yaml"
envsubst < $K8S_YAML > $TMP_YAML
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f $TMP_YAML
rm -f $TMP_YAML

# 部署 Beat
echo "  → 部署 Celery Beat 服务..."
export IMAGE=$BEAT_IMAGE
K8S_YAML="$(pwd)/k8s-deploy/k8s-deployment-beat.yaml"
TMP_YAML="/tmp/k8s-recommender-beat-apply.yaml"
envsubst < $K8S_YAML > $TMP_YAML
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f $TMP_YAML
rm -f $TMP_YAML

# 部署 Consumer
echo "  → 部署 Kafka Consumer 服务..."
export IMAGE=$CONSUMER_IMAGE
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

