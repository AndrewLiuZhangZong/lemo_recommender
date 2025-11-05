#!/bin/bash
set -e

echo "================================================="
echo " 部署 Lemo Recommender 微服务架构 (v2.0)"
echo "================================================="
echo ""
echo "架构说明："
echo "  - 召回服务 (Recall Service) - 端口 8081"
echo "  - 精排服务 (Ranking Service) - 端口 8082"
echo "  - 重排服务 (Reranking Service) - 端口 8083"
echo ""
echo "测试环境配置："
echo "  - 每个服务 1个副本"
echo "  - 总资源: ~2CPU + 8G内存"
echo ""

read -p "是否继续部署？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "取消部署"
    exit 1
fi

echo ""
echo "开始部署微服务..."
echo ""

# 1. 部署召回服务
echo "[1/3] 部署召回服务..."
./k8s-deploy/deploy-recall-service.sh

echo ""
echo "等待召回服务就绪..."
sleep 10

# 2. 部署精排服务
echo "[2/3] 部署精排服务..."
./k8s-deploy/deploy-ranking-service.sh

echo ""
echo "等待精排服务就绪..."
sleep 10

# 3. 部署重排服务
echo "[3/3] 部署重排服务..."
./k8s-deploy/deploy-reranking-service.sh

echo ""
echo "等待重排服务就绪..."
sleep 10

echo ""
echo "================================================="
echo "✅ 所有微服务部署完成！"
echo "================================================="
echo ""

# 查看服务状态
echo "查看服务状态："
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get pods -l version=v2.0

echo ""
echo "查看服务列表："
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get svc | grep -E "recall-service|ranking-service|reranking-service"

echo ""
echo "================================================="
echo "测试服务："
echo "================================================="
echo ""
echo "1. 测试召回服务："
echo "   kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev port-forward svc/recall-service 8081:8081"
echo "   curl http://localhost:8081/health"
echo ""
echo "2. 测试精排服务："
echo "   kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev port-forward svc/ranking-service 8082:8082"
echo "   curl http://localhost:8082/health"
echo ""
echo "3. 测试重排服务："
echo "   kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev port-forward svc/reranking-service 8083:8083"
echo "   curl http://localhost:8083/health"
echo ""
echo "================================================="
echo "下一步："
echo "================================================="
echo ""
echo "修改HTTP API服务，使用BFF模式调用这些微服务"
echo "配置环境变量："
echo "  RECALL_SERVICE_URL=http://recall-service.lemo-dev.svc:8081"
echo "  RANKING_SERVICE_URL=http://ranking-service.lemo-dev.svc:8082"
echo "  RERANKING_SERVICE_URL=http://reranking-service.lemo-dev.svc:8083"
echo ""

