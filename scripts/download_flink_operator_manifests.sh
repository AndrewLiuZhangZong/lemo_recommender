#!/bin/bash
#
# 下载 Flink Kubernetes Operator 安装文件
# 
# 使用场景：在能访问 GitHub 的机器上下载文件，然后传输到目标服务器
# 
# 执行位置：任何能访问 GitHub 的机器
#

set -e

CERT_MANAGER_VERSION="v1.8.2"
FLINK_OPERATOR_VERSION="1.7.0"
FLINK_OPERATOR_RELEASE="release-${FLINK_OPERATOR_VERSION}"

echo "========================================"
echo "下载 Flink Operator 安装文件"
echo "========================================"
echo ""

# 创建临时目录
mkdir -p /tmp/flink-operator-manifests
cd /tmp/flink-operator-manifests

# 下载 cert-manager
echo "1. 下载 cert-manager ${CERT_MANAGER_VERSION}..."
wget -O cert-manager.yaml \
    "https://github.com/cert-manager/cert-manager/releases/download/${CERT_MANAGER_VERSION}/cert-manager.yaml" || {
    echo "✗ 下载 cert-manager 失败"
    exit 1
}
echo "✓ cert-manager 下载完成"
echo ""

# 下载 Flink Operator
echo "2. 下载 Flink Kubernetes Operator ${FLINK_OPERATOR_VERSION}..."
wget -O flink-kubernetes-operator.yaml \
    "https://github.com/apache/flink-kubernetes-operator/releases/download/${FLINK_OPERATOR_RELEASE}/flink-kubernetes-operator-${FLINK_OPERATOR_VERSION}.yaml" || {
    echo "✗ 下载 Flink Operator 失败"
    exit 1
}
echo "✓ Flink Operator 下载完成"
echo ""

echo "========================================"
echo "✓ 所有文件下载完成"
echo "========================================"
echo ""
echo "文件位置："
ls -lh /tmp/flink-operator-manifests/
echo ""
echo "下一步："
echo "1. 将文件传输到目标服务器："
echo "   scp /tmp/flink-operator-manifests/*.yaml root@your-server:/tmp/"
echo ""
echo "2. 在目标服务器上执行离线安装："
echo "   bash scripts/install_flink_operator_offline.sh"
echo ""

