#!/bin/bash
#
# Flink Kubernetes Operator 离线安装脚本
# 
# 使用场景：当所有在线下载源都无法访问时使用
# 
# 使用方法：
# 1. 在能访问 GitHub 的机器上执行：
#    bash scripts/download_flink_operator_manifests.sh
# 
# 2. 将下载的文件传输到服务器：
#    scp manifests/*.yaml root@your-server:/tmp/
# 
# 3. 在服务器上执行本脚本：
#    bash scripts/install_flink_operator_offline.sh
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
    exit 1
fi

echo "使用 kubeconfig: $KUBECONFIG"
export KUBECONFIG

echo "========================================"
echo "Flink Kubernetes Operator 离线安装"
echo "========================================"
echo ""

# 检查文件是否存在
if [ ! -f "/tmp/cert-manager.yaml" ]; then
    echo "✗ /tmp/cert-manager.yaml 不存在"
    echo "请先下载文件：bash scripts/download_flink_operator_manifests.sh"
    exit 1
fi

if [ ! -f "/tmp/flink-kubernetes-operator.yaml" ]; then
    echo "✗ /tmp/flink-kubernetes-operator.yaml 不存在"
    echo "请先下载文件：bash scripts/download_flink_operator_manifests.sh"
    exit 1
fi

# 1. 安装 cert-manager
echo "步骤 1/4: 安装 cert-manager..."
kubectl apply -f /tmp/cert-manager.yaml

echo ""
echo "等待 cert-manager 就绪（最多5分钟）..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s || {
    echo "⚠️  cert-manager Pod 启动超时，请检查："
    kubectl get pods -n cert-manager
    exit 1
}

echo "✓ cert-manager 安装完成"
echo ""

# 2. 创建命名空间
echo "步骤 2/4: 创建 flink-operator-system 命名空间..."
kubectl create namespace flink-operator-system || echo "命名空间已存在"
echo "✓ 命名空间创建完成"
echo ""

# 3. 安装 Flink Operator
echo "步骤 3/4: 安装 Flink Kubernetes Operator..."
kubectl apply -f /tmp/flink-kubernetes-operator.yaml
echo "✓ Flink Operator 安装完成"
echo ""

# 4. 验证安装
echo "步骤 4/4: 验证 Flink Operator 安装..."
echo ""

echo "等待 Operator Pod 就绪（最多5分钟）..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=flink-kubernetes-operator \
    -n flink-operator-system --timeout=300s || {
    echo "⚠️  Flink Operator Pod 启动超时，请检查："
    kubectl get pods -n flink-operator-system
    kubectl describe pod -l app.kubernetes.io/name=flink-kubernetes-operator -n flink-operator-system
    exit 1
}

echo ""
echo "检查 CRD 是否安装..."
kubectl get crd | grep flink || {
    echo "✗ FlinkDeployment CRD 未找到，安装失败"
    exit 1
}

echo ""
echo "========================================"
echo "✓ Flink Kubernetes Operator 安装成功！"
echo "========================================"
echo ""
echo "验证命令："
echo "  kubectl get pods -n flink-operator-system"
echo "  kubectl get crd | grep flink"
echo ""
echo "下一步：执行 bash scripts/deploy_operator_mode.sh"
echo ""

