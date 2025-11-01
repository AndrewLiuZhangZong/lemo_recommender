#!/bin/bash
set -e

# 配置项（请根据实际情况修改）
ACR_REGISTRY="registry.cn-beijing.aliyuncs.com"
ACR_NAMESPACE="lemo_zls"
ACR_IMAGE="lemo-service-recommender-beat"
ACR_TAG="$(date +%Y-%m-%d-%H-%M-%S)"
ACR_USERNAME="北京乐莫科技"
ACR_PASSWORD="Andrew1870361"
KUBECONFIG_FILE="$(pwd)/k8s-deploy/k3s-jd-config.yaml"
K8S_YAML="$(pwd)/k8s-deploy/k8s-deployment-beat.yaml"
TMP_YAML="/tmp/k8s-recommender-beat-apply.yaml"
NAMESPACE="lemo-dev"

IMAGE="$ACR_REGISTRY/$ACR_NAMESPACE/$ACR_IMAGE:$ACR_TAG"

echo "========================================="
echo "部署 Celery Beat 服务"
echo "========================================="

# 1. 构建镜像（跨平台构建 AMD64）
echo "[1/5] 本地构建 Docker 镜像（AMD64 平台）..."
docker buildx build --platform linux/amd64 -t $IMAGE --load .

echo "[2/5] 登录阿里云ACR..."
docker login $ACR_REGISTRY -u "$ACR_USERNAME" -p "$ACR_PASSWORD"

echo "[3/5] 推送镜像到ACR..."
docker push $IMAGE

# 4. 删除原有 Deployment（如果存在）
echo "[4/5] 删除原有 Beat Deployment（如存在）..."
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE delete deployment lemo-service-recommender-beat || true

# 5. 用envsubst替换镜像变量，apply到K3s
echo "[5/5] 应用 Beat K8S部署文件..."
export IMAGE
envsubst < $K8S_YAML > $TMP_YAML
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f $TMP_YAML

echo ""
echo "✅ Beat 服务部署完成！"
echo ""
echo "查看 Beat 状态："
echo "  kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE get pods -l app=lemo-service-recommender-beat"
echo ""
echo "查看 Beat 日志："
echo "  kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE logs -f deployment/lemo-service-recommender-beat"
echo ""
echo "查看定时任务调度状态："
echo "  kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE exec -it deployment/lemo-service-recommender-beat -- celery -A app.tasks.celery_app inspect scheduled"
echo ""

# 删除临时文件
rm -f $TMP_YAML

