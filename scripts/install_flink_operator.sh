#!/bin/bash
#
# Flink Kubernetes Operator 安装脚本
# 
# 执行位置：服务器2 (K8s 服务器)
# 执行用户：root 或有 kubectl 权限的用户
#

set -e

KUBECONFIG="/root/k3s-jd-config.yaml"

echo "========================================"
echo "Flink Kubernetes Operator 安装脚本"
echo "========================================"
echo ""

# 1. 安装 cert-manager
echo "步骤 1/4: 安装 cert-manager..."
echo "cert-manager 是 Flink Operator 的依赖，用于管理 TLS 证书"
echo ""

kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.8.2/cert-manager.yaml --kubeconfig="$KUBECONFIG"

echo ""
echo "等待 cert-manager 就绪（最多5分钟）..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s --kubeconfig="$KUBECONFIG" || {
    echo "⚠️  cert-manager Pod 启动超时，请检查："
    kubectl get pods -n cert-manager --kubeconfig="$KUBECONFIG"
    exit 1
}

echo "✓ cert-manager 安装完成"
echo ""

# 2. 创建 Flink Operator 命名空间
echo "步骤 2/4: 创建 flink-operator-system 命名空间..."
kubectl create namespace flink-operator-system --kubeconfig="$KUBECONFIG" || echo "命名空间已存在"
echo "✓ 命名空间创建完成"
echo ""

# 3. 添加 Helm 仓库（如果已安装 Helm）
echo "步骤 3/4: 检查 Helm 是否安装..."
if command -v helm &> /dev/null; then
    echo "✓ Helm 已安装"
    echo ""
    echo "添加 Flink Operator Helm 仓库..."
    helm repo add flink-operator-repo https://downloads.apache.org/flink/flink-kubernetes-operator-1.7.0/
    helm repo update
    
    echo ""
    echo "使用 Helm 安装 Flink Kubernetes Operator..."
    helm install flink-kubernetes-operator flink-operator-repo/flink-kubernetes-operator \
      --namespace flink-operator-system \
      --set webhook.create=false \
      --kubeconfig="$KUBECONFIG"
    
    echo "✓ Flink Operator 安装完成（通过 Helm）"
else
    echo "⚠️  Helm 未安装，使用 kubectl 直接安装..."
    echo ""
    
    # 下载并安装 Operator YAML
    echo "下载 Flink Operator manifests..."
    wget -O /tmp/flink-kubernetes-operator-1.7.0.yaml \
        https://github.com/apache/flink-kubernetes-operator/releases/download/release-1.7.0/flink-kubernetes-operator-1.7.0.yaml
    
    echo "安装 Flink Operator..."
    kubectl apply -f /tmp/flink-kubernetes-operator-1.7.0.yaml --kubeconfig="$KUBECONFIG"
    
    echo "✓ Flink Operator 安装完成（通过 kubectl）"
fi

echo ""

# 4. 验证安装
echo "步骤 4/4: 验证 Flink Operator 安装..."
echo ""

echo "等待 Operator Pod 就绪（最多5分钟）..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=flink-kubernetes-operator \
    -n flink-operator-system --timeout=300s --kubeconfig="$KUBECONFIG" || {
    echo "⚠️  Flink Operator Pod 启动超时，请检查："
    kubectl get pods -n flink-operator-system --kubeconfig="$KUBECONFIG"
    kubectl describe pod -l app.kubernetes.io/name=flink-kubernetes-operator -n flink-operator-system --kubeconfig="$KUBECONFIG"
    exit 1
}

echo ""
echo "检查 CRD 是否安装..."
kubectl get crd | grep flink --kubeconfig="$KUBECONFIG" || {
    echo "✗ FlinkDeployment CRD 未找到，安装失败"
    exit 1
}

echo ""
echo "========================================"
echo "✓ Flink Kubernetes Operator 安装成功！"
echo "========================================"
echo ""
echo "验证命令："
echo "  kubectl get pods -n flink-operator-system --kubeconfig=$KUBECONFIG"
echo "  kubectl get crd | grep flink --kubeconfig=$KUBECONFIG"
echo ""
echo "下一步：执行阶段2 - 代码改造"
echo ""

