#!/bin/bash
set -e

# 配置项（请根据实际情况修改）
ACR_REGISTRY="registry.cn-beijing.aliyuncs.com"
ACR_NAMESPACE="lemo_zls"
ACR_IMAGE="lemo-service-recommender"  # 推荐服务镜像名
ACR_TAG="$(date +%Y-%m-%d-%H-%M-%S)"  # 用时间戳做唯一tag，格式：yyyy-MM-dd-HH-mm-ss
ACR_USERNAME="北京乐莫科技"   # ACR用户名（如阿里云账号ID或自定义）
ACR_PASSWORD="Andrew1870361"  # ACR密码（建议用环境变量或交互输入）
KUBECONFIG_FILE="$(pwd)/k8s-deploy/k3s-jd-config.yaml"
K8S_YAML="$(pwd)/k8s-deploy/k8s-deployment.yaml"  # K8S配置文件路径
TMP_YAML="/tmp/k8s-recommender-deploy-apply.yaml"
NAMESPACE="lemo-dev"

IMAGE="$ACR_REGISTRY/$ACR_NAMESPACE/$ACR_IMAGE:$ACR_TAG"

# 1. 构建镜像（跨平台构建 AMD64）

echo "[1/5] 本地构建 Docker 镜像（AMD64 平台）..."
docker buildx build --platform linux/amd64 -t $IMAGE --load .

echo "[2/5] 登录阿里云ACR..."
docker login $ACR_REGISTRY -u "$ACR_USERNAME" -p "$ACR_PASSWORD"

echo "[3/5] 推送镜像到ACR..."
docker push $IMAGE

# 4. 创建/更新K8S拉取镜像secret（只需首次或密码变更时执行）
# echo "[可选] 创建K8S拉取镜像secret..."
# kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE create secret docker-registry regcred \
#   --docker-server=$ACR_REGISTRY \
#   --docker-username=$ACR_USERNAME \
#   --docker-password=$ACR_PASSWORD || true

# 5. 删除原有Service（避免端口冲突）
echo "[4/5] 删除原有Service（如存在）..."
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE delete svc lemo-service-recommender || true
kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE delete svc lemo-service-recommender-grpc || true

# 6. 用envsubst替换镜像变量，apply到K3s

echo "[5/5] 应用K8S部署文件..."
export IMAGE
envsubst < $K8S_YAML > $TMP_YAML
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f $TMP_YAML

echo "部署完成！可用如下命令查看状态："
echo "kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE get pods -l app=lemo-service-recommender"
echo "kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE get svc -l app=lemo-service-recommender"
echo "kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE logs -f deployment/lemo-service-recommender-http"
echo "kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE logs -f deployment/lemo-service-recommender-grpc"

# 删除临时文件
rm -f $TMP_YAML

