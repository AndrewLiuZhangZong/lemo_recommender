#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================================="
echo " 部署 Lemo Recommender v2.0 完整架构"
echo "================================================="
echo ""
echo "v2.0架构 - 13个微服务："
echo ""
echo "【在线服务层】7个"
echo "  1. BFF (Recommender) - HTTP+gRPC入口 - 端口8080"
echo "  2. Recall Service - 召回服务 - 端口8081"
echo "  3. Ranking Service - 精排服务 - 端口8082"
echo "  4. Reranking Service - 重排服务 - 端口8083"
echo "  5. User Service - 用户服务 - 端口8084"
echo "  6. Item Service - 物品服务 - 端口8085"
echo "  7. Behavior Service - 行为服务 - 端口8086"
echo ""
echo "【离线服务层】3个"
echo "  8. Model Training - 模型训练 - 端口8091"
echo "  9. Feature Engineering - 特征工程 - 端口8092"
echo "  10. Vector Generation - 向量生成 - 端口8093"
echo ""
echo "【实时服务层】3个"
echo "  11. Flink Realtime - 实时特征计算"
echo "  12. Data Sync - 数据同步"
echo "  13. Realtime Stream - 实时推荐流"
echo ""
echo "【后台服务】已部署"
echo "  - Worker (Celery异步任务)"
echo "  - Beat (定时任务)"
echo "  - Consumer (Kafka消费)"
echo ""

read -p "是否继续部署全部13个服务？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "取消部署"
    exit 1
fi

echo ""
echo "开始部署v2.0微服务架构..."
echo ""

# 1. 部署在线服务层（7个）
echo "========================================"
echo "【1/3】部署在线服务层（7个服务）"
echo "========================================"
echo ""

echo "[1/7] 部署召回服务..."
bash "$SCRIPT_DIR/deploy-recall-service.sh"
sleep 5

echo ""
echo "[2/7] 部署精排服务..."
bash "$SCRIPT_DIR/deploy-ranking-service.sh"
sleep 5

echo ""
echo "[3/7] 部署重排服务..."
bash "$SCRIPT_DIR/deploy-reranking-service.sh"
sleep 5

echo ""
echo "[4/7] 部署用户服务..."
bash "$SCRIPT_DIR/deploy-user-service.sh"
sleep 5

echo ""
echo "[5/7] 部署物品服务..."
bash "$SCRIPT_DIR/deploy-item-service.sh"
sleep 5

echo ""
echo "[6/7] 部署行为服务..."
bash "$SCRIPT_DIR/deploy-behavior-service.sh"
sleep 5

echo ""
echo "[7/7] 部署BFF服务（HTTP+gRPC入口）..."
bash "$SCRIPT_DIR/deploy-http-grpc-service.sh"
sleep 5

# 2. 部署离线服务层（3个）
echo ""
echo "========================================"
echo "【2/3】部署离线服务层（3个服务）"
echo "========================================"
echo ""

echo "批量部署离线计算服务..."
bash "$SCRIPT_DIR/deploy-offline-services.sh"
sleep 5

# 3. 部署实时服务层（3个）
echo ""
echo "========================================"
echo "【3/3】部署实时服务层（3个服务）"
echo "========================================"
echo ""

echo "批量部署实时服务..."
bash "$SCRIPT_DIR/deploy-realtime-services.sh"
sleep 5

echo ""
echo "================================================="
echo "✅ v2.0架构部署完成！"
echo "================================================="
echo ""

# 设置kubeconfig
KUBECONFIG_PATH="$SCRIPT_DIR/k3s-jd-config.yaml"
if [ -f "$KUBECONFIG_PATH" ]; then
    export KUBECONFIG="$KUBECONFIG_PATH"
fi

# 查看服务状态
echo "【在线服务层】状态："
kubectl get pods -n lemo-dev | grep -E "recall|ranking|reranking|user-service|item-service|behavior-service|http-grpc" || true

echo ""
echo "【离线服务层】状态："
kubectl get pods -n lemo-dev | grep -E "model-training|feature-engineering|vector-generation" || true

echo ""
echo "【实时服务层】状态："
kubectl get pods -n lemo-dev | grep -E "flink-realtime|data-sync|realtime-stream" || true

echo ""
echo "【后台服务】状态："
kubectl get pods -n lemo-dev | grep -E "worker|beat|consumer" || true

echo ""
echo "================================================="
echo "查看所有服务："
echo "================================================="
echo ""
kubectl get svc -n lemo-dev | grep lemo-service-recommender || true

echo ""
echo "================================================="
echo "健康检查："
echo "================================================="
echo ""
echo "在线服务端口转发（使用以下命令测试）："
echo ""
echo "  # 召回服务"
echo "  kubectl port-forward -n lemo-dev svc/lemo-service-recommender-recall 8081:8081"
echo ""
echo "  # 精排服务"
echo "  kubectl port-forward -n lemo-dev svc/lemo-service-recommender-ranking 8082:8082"
echo ""
echo "  # 重排服务"
echo "  kubectl port-forward -n lemo-dev svc/lemo-service-recommender-reranking 8083:8083"
echo ""
echo "  # BFF服务（HTTP API入口）"
echo "  kubectl port-forward -n lemo-dev svc/lemo-service-recommender-http 8080:8080"
echo ""
echo "================================================="
echo "Istio服务网格（可选）："
echo "================================================="
echo ""
echo "如需启用Istio熔断/限流/链路追踪，运行："
echo "  bash k8s-deploy/istio/install-istio.sh"
echo ""
echo "================================================="
echo "v2.0架构已就绪！🎉"
echo "================================================="
echo ""

