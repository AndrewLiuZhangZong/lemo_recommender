#!/bin/bash
#
# Flink Operator 模式完整部署脚本
#
# 执行位置：服务器2 (K8s 服务器)
# 执行用户：root 或有 kubectl 权限的用户
#

set -e

KUBECONFIG="/root/k3s-jd-config.yaml"

echo "========================================"
echo "Flink Operator 模式部署脚本"
echo "========================================"
echo ""

# 1. 应用 K8s 配置
echo "步骤 1/3: 更新 K8s 配置..."
echo ""

kubectl apply -f /path/to/k8s-deploy/k8s-deployment-http-grpc.yaml --kubeconfig="$KUBECONFIG"
kubectl apply -f /path/to/k8s-deploy/k8s-deployment-worker.yaml --kubeconfig="$KUBECONFIG"
kubectl apply -f /path/to/k8s-deploy/k8s-deployment-beat.yaml --kubeconfig="$KUBECONFIG"
kubectl apply -f /path/to/k8s-deploy/k8s-deployment-consumer.yaml --kubeconfig="$KUBECONFIG"

echo "✓ K8s 配置已更新"
echo ""

# 2. 重启服务
echo "步骤 2/3: 重启推荐服务..."
echo ""

kubectl rollout restart deployment/lemo-service-recommender-http -n lemo-dev --kubeconfig="$KUBECONFIG"
kubectl rollout restart deployment/lemo-service-recommender-grpc -n lemo-dev --kubeconfig="$KUBECONFIG"
kubectl rollout restart deployment/lemo-service-recommender-worker -n lemo-dev --kubeconfig="$KUBECONFIG"
kubectl rollout restart deployment/lemo-service-recommender-beat -n lemo-dev --kubeconfig="$KUBECONFIG"
kubectl rollout restart deployment/lemo-service-recommender-consumer -n lemo-dev --kubeconfig="$KUBECONFIG"

echo "✓ 服务重启中..."
echo ""

# 3. 等待部署完成
echo "步骤 3/3: 等待部署完成（最多5分钟）..."
echo ""

kubectl rollout status deployment/lemo-service-recommender-http -n lemo-dev --timeout=300s --kubeconfig="$KUBECONFIG"
kubectl rollout status deployment/lemo-service-recommender-grpc -n lemo-dev --timeout=300s --kubeconfig="$KUBECONFIG"

echo ""
echo "========================================"
echo "✓ Flink Operator 模式部署完成！"
echo "========================================"
echo ""
echo "验证命令："
echo "  # 查看推荐服务日志"
echo "  kubectl logs -f deployment/lemo-service-recommender-http -n lemo-dev --kubeconfig=$KUBECONFIG"
echo ""
echo "  # 查看 FlinkDeployment CRD"
echo "  kubectl get flinkdeployments -n lemo-dev --kubeconfig=$KUBECONFIG"
echo ""
echo "  # 提交测试作业并查看"
echo "  kubectl get flinkdeployments -n lemo-dev -w --kubeconfig=$KUBECONFIG"
echo ""

