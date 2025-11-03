#!/bin/bash
#
# Flink Kubernetes Operator 安装脚本
# 
# 执行位置：服务器2 (K8s 服务器 117.72.196.41)
# 执行用户：root 或有 kubectl 权限的用户
#
# 使用方法：
#   bash scripts/install_flink_operator.sh
#

set -e

echo "========================================"
echo "Flink Kubernetes Operator 安装"
echo "========================================"
echo ""

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

# 验证 kubectl 连接
echo ""
echo "验证 K8s 连接..."
kubectl get nodes || {
    echo "✗ 无法连接到 K8s 集群"
    echo "请检查："
    echo "  1. kubeconfig 文件是否正确"
    echo "  2. K8s 集群是否运行"
    echo "  3. 网络连接是否正常"
    exit 1
}
echo "✓ K8s 连接正常"

echo ""

# 1. 安装 cert-manager
echo "步骤 1/4: 安装 cert-manager..."
echo "cert-manager 是 Flink Operator 的依赖，用于管理 TLS 证书"
echo ""

# 使用国内镜像加速
echo "使用阿里云镜像加速..."
CERT_MANAGER_VERSION="v1.8.2"
CERT_MANAGER_URL="https://ghproxy.com/https://github.com/cert-manager/cert-manager/releases/download/${CERT_MANAGER_VERSION}/cert-manager.yaml"

# 检测下载工具
if command -v curl &> /dev/null; then
    DOWNLOAD_CMD="curl -fsSL -o"
elif command -v wget &> /dev/null; then
    DOWNLOAD_CMD="wget -O"
else
    echo "✗ 需要 curl 或 wget"
    exit 1
fi

# 下载到本地
$DOWNLOAD_CMD /tmp/cert-manager.yaml "$CERT_MANAGER_URL" || {
    echo "⚠️  从镜像源下载失败，尝试直接访问 GitHub..."
    $DOWNLOAD_CMD /tmp/cert-manager.yaml "https://github.com/cert-manager/cert-manager/releases/download/${CERT_MANAGER_VERSION}/cert-manager.yaml" || {
        echo "✗ 下载 cert-manager 失败"
        exit 1
    }
}

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

# 2. 创建 Flink Operator 命名空间
echo "步骤 2/4: 创建 flink-operator-system 命名空间..."
kubectl create namespace flink-operator-system || echo "命名空间已存在"
echo "✓ 命名空间创建完成"
echo ""

# 3. 安装 Flink Kubernetes Operator
echo "步骤 3/4: 安装 Flink Kubernetes Operator..."
echo ""

FLINK_OPERATOR_VERSION="1.7.0"
FLINK_OPERATOR_RELEASE="release-${FLINK_OPERATOR_VERSION}"

# 优先使用 kubectl 直接安装（更简单可靠）
echo "下载 Flink Operator manifests..."
FLINK_OPERATOR_URL="https://ghproxy.com/https://github.com/apache/flink-kubernetes-operator/releases/download/${FLINK_OPERATOR_RELEASE}/flink-kubernetes-operator-${FLINK_OPERATOR_VERSION}.yaml"

$DOWNLOAD_CMD /tmp/flink-kubernetes-operator.yaml "$FLINK_OPERATOR_URL" || {
    echo "⚠️  从镜像源下载失败，尝试直接访问 GitHub..."
    $DOWNLOAD_CMD /tmp/flink-kubernetes-operator.yaml \
        "https://github.com/apache/flink-kubernetes-operator/releases/download/${FLINK_OPERATOR_RELEASE}/flink-kubernetes-operator-${FLINK_OPERATOR_VERSION}.yaml" || {
        echo "⚠️  GitHub 访问失败，尝试从 Apache 官网下载..."
        $DOWNLOAD_CMD /tmp/flink-kubernetes-operator.yaml \
            "https://archive.apache.org/dist/flink/flink-kubernetes-operator-${FLINK_OPERATOR_VERSION}/flink-kubernetes-operator-${FLINK_OPERATOR_VERSION}.yaml" || {
            echo "✗ 所有下载源均失败"
            exit 1
        }
    }
}

echo "安装 Flink Operator..."
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
echo "  export KUBECONFIG=$KUBECONFIG"
echo "  kubectl get pods -n flink-operator-system"
echo "  kubectl get crd | grep flink"
echo ""
echo "下一步："
echo "  bash scripts/deploy_operator_mode.sh  # 部署推荐服务"
echo ""

