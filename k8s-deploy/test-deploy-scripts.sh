#!/bin/bash
# 测试部署脚本的基本逻辑（不实际执行 Docker 和 K8s 操作）

set -e

echo "========================================="
echo "测试部署脚本配置"
echo "========================================="
echo ""

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查脚本文件
check_script() {
    local script=$1
    local service=$2
    
    echo -n "检查 $service 脚本... "
    
    if [ ! -f "$script" ]; then
        echo -e "${RED}❌ 文件不存在${NC}"
        return 1
    fi
    
    # 检查语法
    if ! bash -n "$script" 2>/dev/null; then
        echo -e "${RED}❌ 语法错误${NC}"
        return 1
    fi
    
    # 检查关键变量
    if ! grep -q "ACR_IMAGE=" "$script"; then
        echo -e "${RED}❌ 缺少 ACR_IMAGE${NC}"
        return 1
    fi
    
    if ! grep -q "K8S_YAML=" "$script"; then
        echo -e "${RED}❌ 缺少 K8S_YAML${NC}"
        return 1
    fi
    
    if ! grep -q "IMAGE=" "$script"; then
        echo -e "${RED}❌ 缺少 IMAGE${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓${NC}"
    return 0
}

# 检查 K8s YAML 文件
check_yaml() {
    local yaml=$1
    local service=$2
    
    echo -n "检查 $service K8s 配置... "
    
    if [ ! -f "$yaml" ]; then
        echo -e "${RED}❌ 文件不存在${NC}"
        return 1
    fi
    
    # 检查是否有 ${IMAGE} 占位符
    if ! grep -q '\${IMAGE}' "$yaml"; then
        echo -e "${YELLOW}⚠️  未找到 \${IMAGE} 占位符${NC}"
    fi
    
    # 检查 deployment 名称
    local deployment_name=$(grep -E "^  name:" "$yaml" | grep -v ConfigMap | grep -v Service | grep -v ServiceAccount | grep -v Role | head -1 | awk '{print $2}')
    if [ -z "$deployment_name" ]; then
        echo -e "${YELLOW}⚠️  未找到 deployment 名称${NC}"
    else
        echo -e "${GREEN}✓ (deployment: $deployment_name)${NC}"
    fi
    
    return 0
}

# 验证脚本和 YAML 的匹配
verify_match() {
    local script=$1
    local expected_yaml=$2
    local service=$3
    
    echo -n "验证 $service 脚本和 YAML 匹配... "
    
    # 从脚本中提取 K8S_YAML 路径
    local script_yaml=$(grep 'K8S_YAML=' "$script" | head -1 | sed "s|.*K8S_YAML=\"\$(pwd)/\(.*\)\"|\1|" | sed "s|\"||g" | sed "s|  # .*||" | xargs)
    
    if [ "$script_yaml" != "$expected_yaml" ]; then
        echo -e "${RED}❌ 不匹配: 脚本指向 $script_yaml，期望 $expected_yaml${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓${NC}"
    return 0
}

# 验证镜像名称
verify_image_name() {
    local script=$1
    local expected_pattern=$2
    local service=$3
    
    echo -n "验证 $service 镜像名称... "
    
    # 从脚本中提取 ACR_IMAGE
    local acr_image=$(grep 'ACR_IMAGE=' "$script" | cut -d'"' -f2)
    
    if ! echo "$acr_image" | grep -q "$expected_pattern"; then
        echo -e "${RED}❌ 不匹配: $acr_image 不符合预期模式 $expected_pattern${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ ($acr_image)${NC}"
    return 0
}

# 验证标签查询
verify_label_query() {
    local script=$1
    local expected_label=$2
    local service=$3
    
    echo -n "验证 $service 标签查询... "
    
    if ! grep -q "$expected_label" "$script"; then
        echo -e "${RED}❌ 未找到标签查询: $expected_label${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓${NC}"
    return 0
}

echo "[1/6] 检查脚本文件..."
check_script "k8s-deploy/deploy-worker-service.sh" "Worker"
check_script "k8s-deploy/deploy-beat-service.sh" "Beat"
check_script "k8s-deploy/deploy-consumer-service.sh" "Consumer"
check_script "k8s-deploy/deploy-http-grpc-service.sh" "HTTP/gRPC"
echo ""

echo "[2/6] 检查 K8s YAML 文件..."
check_yaml "k8s-deploy/k8s-deployment-worker.yaml" "Worker"
check_yaml "k8s-deploy/k8s-deployment-beat.yaml" "Beat"
check_yaml "k8s-deploy/k8s-deployment-consumer.yaml" "Consumer"
check_yaml "k8s-deploy/k8s-deployment-http-grpc.yaml" "HTTP/gRPC"
echo ""

echo "[3/6] 验证脚本和 YAML 匹配..."
verify_match "k8s-deploy/deploy-worker-service.sh" "k8s-deploy/k8s-deployment-worker.yaml" "Worker"
verify_match "k8s-deploy/deploy-beat-service.sh" "k8s-deploy/k8s-deployment-beat.yaml" "Beat"
verify_match "k8s-deploy/deploy-consumer-service.sh" "k8s-deploy/k8s-deployment-consumer.yaml" "Consumer"
verify_match "k8s-deploy/deploy-http-grpc-service.sh" "k8s-deploy/k8s-deployment-http-grpc.yaml" "HTTP/gRPC"
echo ""

echo "[4/6] 验证镜像名称..."
verify_image_name "k8s-deploy/deploy-worker-service.sh" "lemo-service-recommender-worker" "Worker"
verify_image_name "k8s-deploy/deploy-beat-service.sh" "lemo-service-recommender-beat" "Beat"
verify_image_name "k8s-deploy/deploy-consumer-service.sh" "lemo-service-recommender-consumer" "Consumer"
verify_image_name "k8s-deploy/deploy-http-grpc-service.sh" "lemo-service-recommender" "HTTP/gRPC"
echo ""

echo "[5/6] 验证标签查询..."
verify_label_query "k8s-deploy/deploy-worker-service.sh" "app=lemo-service-recommender-worker" "Worker"
verify_label_query "k8s-deploy/deploy-beat-service.sh" "app=lemo-service-recommender-beat" "Beat"
verify_label_query "k8s-deploy/deploy-consumer-service.sh" "app=lemo-service-recommender-consumer" "Consumer"
verify_label_query "k8s-deploy/deploy-http-grpc-service.sh" "app=lemo-service-recommender" "HTTP/gRPC"
echo ""

echo "[6/6] 验证 Deployment 名称..."
echo -n "检查 Worker deployment 名称... "
if grep -q "delete deployment lemo-service-recommender-worker" k8s-deploy/deploy-worker-service.sh; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}❌${NC}"
fi

echo -n "检查 Beat deployment 名称... "
if grep -q "delete deployment lemo-service-recommender-beat" k8s-deploy/deploy-beat-service.sh; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}❌${NC}"
fi

echo -n "检查 Consumer deployment 名称... "
if grep -q "delete deployment lemo-service-recommender-consumer" k8s-deploy/deploy-consumer-service.sh; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}❌${NC}"
fi

echo ""
echo "========================================="
echo -e "${GREEN}✅ 所有检查完成！${NC}"
echo "========================================="
echo ""
echo "下一步："
echo "  1. 确保 Docker daemon 正在运行"
echo "  2. 确保可以访问 K8s 集群"
echo "  3. 运行相应的部署脚本进行实际部署"
echo ""

