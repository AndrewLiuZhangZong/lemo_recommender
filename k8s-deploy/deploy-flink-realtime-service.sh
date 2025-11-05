#!/bin/bash
# 部署Flink实时特征服务到K8s集群

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${NAMESPACE:-lemo-dev}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "=========================================="
echo "  部署Flink实时特征服务到K8s"
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

# 检查Flink Operator是否安装
echo "2. 检查Flink Operator..."
if ! kubectl get crd flinkdeployments.flink.apache.org &> /dev/null; then
    echo "❌ 错误: Flink Operator未安装"
    echo "   请先运行: bash scripts/install_flink_operator.sh"
    exit 1
fi

# 应用ConfigMap（如果存在）
if [ -f "$SCRIPT_DIR/configmap-services.yaml" ]; then
    echo "3. 应用ConfigMap配置..."
    kubectl apply -f "$SCRIPT_DIR/configmap-services.yaml" -n "$NAMESPACE"
fi

# 部署Flink实时特征服务
echo "4. 部署Flink实时特征服务..."
kubectl apply -f "$SCRIPT_DIR/flink-deployment-realtime-service.yaml" -n "$NAMESPACE"

# 等待FlinkDeployment创建完成
echo "5. 等待Flink作业启动（可能需要1-2分钟）..."
sleep 10

# 检查FlinkDeployment状态
echo "6. 检查FlinkDeployment状态..."
kubectl get flinkdeployment flink-realtime-features -n "$NAMESPACE"

echo ""
echo "=========================================="
echo "  ✅ Flink实时特征服务部署成功！"
echo "=========================================="
echo ""
echo "查看FlinkDeployment状态:"
echo "  kubectl get flinkdeployment flink-realtime-features -n $NAMESPACE"
echo ""
echo "查看JobManager日志:"
echo "  kubectl logs -f -n $NAMESPACE -l app=flink-realtime-features,component=jobmanager"
echo ""
echo "查看TaskManager日志:"
echo "  kubectl logs -f -n $NAMESPACE -l app=flink-realtime-features,component=taskmanager"
echo ""
echo "查看所有Flink Pod:"
echo "  kubectl get pods -n $NAMESPACE -l app=flink-realtime-features"
echo ""

