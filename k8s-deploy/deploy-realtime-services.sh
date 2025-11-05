#!/bin/bash
# 部署所有实时服务到K8s集群
# 包含: Flink Realtime, Data Sync, Realtime Stream

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${NAMESPACE:-lemo-dev}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "=========================================="
echo "  部署实时服务到K8s"
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

# 部署数据同步服务
echo ""
echo "3. 部署数据同步服务..."
kubectl apply -f "$SCRIPT_DIR/k8s-deployment-data-sync-service.yaml" -n "$NAMESPACE"
echo "   等待服务就绪..."
kubectl rollout status deployment/lemo-service-recommender-data-sync -n "$NAMESPACE" --timeout=300s

# 部署实时推荐流服务
echo ""
echo "4. 部署实时推荐流服务..."
kubectl apply -f "$SCRIPT_DIR/k8s-deployment-realtime-stream-service.yaml" -n "$NAMESPACE"
echo "   等待服务就绪..."
kubectl rollout status deployment/lemo-service-recommender-realtime-stream -n "$NAMESPACE" --timeout=300s

# 部署Flink实时特征服务
echo ""
echo "5. 部署Flink实时特征服务..."
if ! kubectl get crd flinkdeployments.flink.apache.org &> /dev/null; then
    echo "⚠️  警告: Flink Operator未安装，跳过Flink服务部署"
    echo "   请先运行: bash scripts/install_flink_operator.sh"
else
    kubectl apply -f "$SCRIPT_DIR/flink-deployment-realtime-service.yaml" -n "$NAMESPACE"
    echo "   Flink作业已提交，等待启动..."
    sleep 10
fi

echo ""
echo "=========================================="
echo "  ✅ 实时服务部署成功！"
echo "=========================================="
echo ""
echo "已部署的服务:"
echo "  1. 数据同步服务 (Data Sync) - Celery后台任务"
echo "  2. 实时推荐流服务 (Realtime Stream) - Kafka消费"
if kubectl get crd flinkdeployments.flink.apache.org &> /dev/null; then
echo "  3. Flink实时特征服务 (Flink Realtime) - FlinkDeployment"
fi
echo ""
echo "查看所有实时服务状态:"
echo "  kubectl get pods -n $NAMESPACE | grep -E 'data-sync|realtime-stream|flink-realtime'"
echo ""

