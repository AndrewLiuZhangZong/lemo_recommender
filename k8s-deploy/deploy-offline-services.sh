#!/bin/bash
# 部署所有离线计算服务到K8s集群
# 包含: Model Training, Feature Engineering, Vector Generation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${NAMESPACE:-lemo-dev}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "=========================================="
echo "  部署离线计算服务到K8s"
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

# 部署模型训练服务
echo ""
echo "3. 部署模型训练服务..."
kubectl apply -f "$SCRIPT_DIR/k8s-deployment-model-training-service.yaml" -n "$NAMESPACE"
echo "   等待服务就绪..."
kubectl rollout status deployment/lemo-service-recommender-model-training -n "$NAMESPACE" --timeout=300s

# 部署特征工程服务
echo ""
echo "4. 部署特征工程服务..."
kubectl apply -f "$SCRIPT_DIR/k8s-deployment-feature-engineering-service.yaml" -n "$NAMESPACE"
echo "   等待服务就绪..."
kubectl rollout status deployment/lemo-service-recommender-feature-engineering -n "$NAMESPACE" --timeout=300s

# 部署向量生成服务
echo ""
echo "5. 部署向量生成服务..."
kubectl apply -f "$SCRIPT_DIR/k8s-deployment-vector-generation-service.yaml" -n "$NAMESPACE"
echo "   等待服务就绪..."
kubectl rollout status deployment/lemo-service-recommender-vector-generation -n "$NAMESPACE" --timeout=300s

echo ""
echo "=========================================="
echo "  ✅ 离线计算服务部署成功！"
echo "=========================================="
echo ""
echo "已部署的服务:"
echo "  1. 模型训练服务 (Model Training) - 端口8091"
echo "  2. 特征工程服务 (Feature Engineering) - 端口8092"
echo "  3. 向量生成服务 (Vector Generation) - 端口8093"
echo ""
echo "查看所有离线服务状态:"
echo "  kubectl get pods -n $NAMESPACE | grep -E 'model-training|feature-engineering|vector-generation'"
echo ""

