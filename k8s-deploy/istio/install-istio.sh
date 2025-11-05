#!/bin/bash
set -e

echo "================================================="
echo " 安装 Istio Service Mesh"
echo " 对标字节跳动超大规模标准"
echo "================================================="

# 配置
ISTIO_VERSION="1.20.2"
KUBECONFIG_FILE="$(pwd)/k8s-deploy/k3s-jd-config.yaml"
NAMESPACE="lemo-dev"

echo ""
echo "[1/6] 检查 Istio 是否已安装..."
if command -v istioctl &> /dev/null; then
    CURRENT_VERSION=$(istioctl version --short 2>/dev/null | grep "client version" | awk '{print $NF}' || echo "unknown")
    echo "✅ Istio CLI已安装: $CURRENT_VERSION"
else
    echo "❌ Istio CLI未安装，开始安装..."
    
    # 下载istioctl
    echo "下载 Istio $ISTIO_VERSION..."
    curl -L https://istio.io/downloadIstio | ISTIO_VERSION=$ISTIO_VERSION sh -
    
    # 移动到PATH
    sudo cp istio-$ISTIO_VERSION/bin/istioctl /usr/local/bin/
    
    echo "✅ Istio CLI安装完成"
fi

echo ""
echo "[2/6] 安装 Istio 到 K8s 集群..."
istioctl install --set profile=production \
    --kubeconfig=$KUBECONFIG_FILE \
    --set values.global.proxy.resources.requests.cpu=100m \
    --set values.global.proxy.resources.requests.memory=128Mi \
    --set values.global.proxy.resources.limits.cpu=500m \
    --set values.global.proxy.resources.limits.memory=512Mi \
    -y

echo ""
echo "[3/6] 创建命名空间并启用自动注入..."
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f k8s-deploy/istio/00-namespace.yaml

# 验证自动注入
INJECTION_STATUS=$(kubectl --kubeconfig=$KUBECONFIG_FILE get namespace $NAMESPACE -o jsonpath='{.metadata.labels.istio-injection}')
if [ "$INJECTION_STATUS" == "enabled" ]; then
    echo "✅ Namespace $NAMESPACE 已启用 Istio 自动注入"
else
    echo "❌ 自动注入未启用，手动设置..."
    kubectl --kubeconfig=$KUBECONFIG_FILE label namespace $NAMESPACE istio-injection=enabled --overwrite
fi

echo ""
echo "[4/6] 应用 DestinationRule 配置（熔断、负载均衡）..."
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f k8s-deploy/istio/01-destination-rules.yaml

echo ""
echo "[5/6] 应用 VirtualService 配置（超时、重试）..."
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f k8s-deploy/istio/02-virtual-services.yaml

echo ""
echo "[6/6] 安装可观测性组件..."

# Prometheus
echo "安装 Prometheus..."
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/prometheus.yaml

# Grafana
echo "安装 Grafana..."
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/grafana.yaml

# Jaeger (分布式追踪)
echo "安装 Jaeger..."
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/jaeger.yaml

# Kiali (服务网格可视化)
echo "安装 Kiali..."
kubectl --kubeconfig=$KUBECONFIG_FILE apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/kiali.yaml

echo ""
echo "================================================="
echo "✅ Istio Service Mesh 安装完成！"
echo "================================================="

echo ""
echo "📊 验证安装："
echo "  istioctl --kubeconfig=$KUBECONFIG_FILE verify-install"

echo ""
echo "🎨 访问可观测性工具："
echo ""
echo "  1. Kiali (服务网格可视化):"
echo "     istioctl dashboard kiali --kubeconfig=$KUBECONFIG_FILE"
echo ""
echo "  2. Grafana (监控大盘):"
echo "     istioctl dashboard grafana --kubeconfig=$KUBECONFIG_FILE"
echo ""
echo "  3. Jaeger (分布式追踪):"
echo "     istioctl dashboard jaeger --kubeconfig=$KUBECONFIG_FILE"
echo ""
echo "  4. Prometheus (指标查询):"
echo "     istioctl dashboard prometheus --kubeconfig=$KUBECONFIG_FILE"

echo ""
echo "🔄 重启现有服务以注入 Envoy Sidecar:"
echo "  kubectl --kubeconfig=$KUBECONFIG_FILE -n $NAMESPACE rollout restart deployment"

echo ""
echo "================================================="

