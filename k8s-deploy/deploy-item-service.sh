#!/bin/bash
# 部署物品服务到K8s集群

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${NAMESPACE:-lemo-dev}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "=========================================="
echo "  部署物品服务到K8s"
echo "=========================================="
echo "命名空间: $NAMESPACE"
echo "镜像标签: $IMAGE_TAG"
echo ""

# 检查kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ 错误: kubectl未安装"
    exit 1
fi

# 检查kubeconfig
if [ -z "$KUBECONFIG" ]; then
    if [ -f "$SCRIPT_DIR/k3s-jd-config.yaml" ]; then
        export KUBECONFIG="$SCRIPT_DIR/k3s-jd-config.yaml"
        echo "✓ 使用kubeconfig: $KUBECONFIG"
    else
        echo "⚠️  警告: 未设置KUBECONFIG，使用默认配置"
    fi
fi

# 创建命名空间（如果不存在）
echo "1. 检查命名空间..."
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "   创建命名空间: $NAMESPACE"
    kubectl create namespace "$NAMESPACE"
fi

# 应用ConfigMap（如果存在）
if [ -f "$SCRIPT_DIR/configmap-services.yaml" ]; then
    echo "2. 应用ConfigMap配置..."
    kubectl apply -f "$SCRIPT_DIR/configmap-services.yaml" -n "$NAMESPACE"
fi

# 部署服务
echo "3. 部署物品服务..."
kubectl apply -f "$SCRIPT_DIR/k8s-deployment-item-service.yaml" -n "$NAMESPACE"

# 等待部署完成
echo "4. 等待服务就绪..."
kubectl rollout status deployment/lemo-service-recommender-item -n "$NAMESPACE" --timeout=300s

echo ""
echo "=========================================="
echo "  ✅ 物品服务部署成功！"
echo "=========================================="
echo ""
echo "查看服务状态:"
echo "  kubectl get pods -n $NAMESPACE -l app=lemo-service-recommender-item"
echo ""
echo "查看服务日志:"
echo "  kubectl logs -f -n $NAMESPACE -l app=lemo-service-recommender-item"
echo ""

