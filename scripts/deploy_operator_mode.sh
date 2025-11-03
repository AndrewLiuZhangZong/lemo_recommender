#!/bin/bash
#
# Flink Operator 模式完整部署脚本
#
# 执行位置：服务器2 (K8s 服务器)
# 执行用户：root 或有 kubectl 权限的用户
#

set -e

# 自动检测 kubeconfig 路径
if [ -f "/root/k3s-jd-config.yaml" ]; then
    KUBECONFIG="/root/k3s-jd-config.yaml"
elif [ -f "$(pwd)/k8s-deploy/k3s-jd-config.yaml" ]; then
    KUBECONFIG="$(pwd)/k8s-deploy/k3s-jd-config.yaml"
elif [ -f "/etc/rancher/k3s/k3s.yaml" ]; then
    KUBECONFIG="/etc/rancher/k3s/k3s.yaml"
else
    echo "✗ 找不到 kubeconfig 文件"
    echo "请将 k3s-jd-config.yaml 放到以下位置之一："
    echo "  - /root/k3s-jd-config.yaml"
    echo "  - $(pwd)/k8s-deploy/k3s-jd-config.yaml"
    echo "或者设置 KUBECONFIG 环境变量"
    exit 1
fi

echo "使用 kubeconfig: $KUBECONFIG"
export KUBECONFIG

echo "========================================"
echo "Flink Operator 模式部署脚本"
echo "========================================"
echo ""

# 检测脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "项目根目录: $PROJECT_ROOT"
echo ""

# 1. 应用 K8s 配置
echo "步骤 1/3: 更新 K8s 配置..."
echo ""

kubectl apply -f "$PROJECT_ROOT/k8s-deploy/k8s-deployment-http-grpc.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s-deploy/k8s-deployment-worker.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s-deploy/k8s-deployment-beat.yaml"
kubectl apply -f "$PROJECT_ROOT/k8s-deploy/k8s-deployment-consumer.yaml"

echo "✓ K8s 配置已更新"
echo ""

# 2. 重启服务
echo "步骤 2/3: 重启推荐服务..."
echo ""

kubectl rollout restart deployment/lemo-service-recommender-http -n lemo-dev
kubectl rollout restart deployment/lemo-service-recommender-grpc -n lemo-dev
kubectl rollout restart deployment/lemo-service-recommender-worker -n lemo-dev
kubectl rollout restart deployment/lemo-service-recommender-beat -n lemo-dev
kubectl rollout restart deployment/lemo-service-recommender-consumer -n lemo-dev

echo "✓ 服务重启中..."
echo ""

# 3. 等待部署完成
echo "步骤 3/3: 等待部署完成（最多5分钟）..."
echo ""

kubectl rollout status deployment/lemo-service-recommender-http -n lemo-dev --timeout=300s
kubectl rollout status deployment/lemo-service-recommender-grpc -n lemo-dev --timeout=300s

echo ""
echo "========================================"
echo "✓ Flink Operator 模式部署完成！"
echo "========================================"
echo ""
echo "验证命令："
echo "  # 查看推荐服务日志"
echo "  kubectl logs -f deployment/lemo-service-recommender-http -n lemo-dev"
echo ""
echo "  # 查看 FlinkDeployment CRD"
echo "  kubectl get flinkdeployments -n lemo-dev"
echo ""
echo "  # 提交测试作业并查看"
echo "  kubectl get flinkdeployments -n lemo-dev -w"
echo ""

