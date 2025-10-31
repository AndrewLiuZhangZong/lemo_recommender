#!/bin/bash
# 初始化 Kafka Topics
# 使用 Docker exec 直接在 Kafka 容器中创建 Topic

set -e

echo "========================================"
echo "初始化 Kafka Topics"
echo "========================================"

# Kafka 服务器信息
KAFKA_HOST="111.228.39.41"
KAFKA_PORT="9092"
KAFKA_CONTAINER="lemo-kafka"  # 假设 Kafka 容器名

# 待创建的 Topics
TOPICS=(
  "items-ingest"
  "vlog-items"
  "news-items"
)

echo ""
echo "📡 Kafka 服务器: ${KAFKA_HOST}:${KAFKA_PORT}"
echo "📋 待创建 Topics: ${TOPICS[*]}"
echo ""

# 方案1: 如果能访问 Kafka 容器
if docker ps --format '{{.Names}}' | grep -q "^${KAFKA_CONTAINER}$"; then
  echo "✅ 找到 Kafka 容器: ${KAFKA_CONTAINER}"
  echo ""
  
  for TOPIC in "${TOPICS[@]}"; do
    echo "📝 创建 Topic: ${TOPIC}"
    docker exec ${KAFKA_CONTAINER} /opt/kafka/bin/kafka-topics.sh \
      --bootstrap-server localhost:9092 \
      --create \
      --if-not-exists \
      --topic ${TOPIC} \
      --partitions 3 \
      --replication-factor 1 \
      --config retention.ms=604800000 \
      && echo "✅ 成功: ${TOPIC}" || echo "⚠️  可能已存在: ${TOPIC}"
  done
  
  echo ""
  echo "========================================"
  echo "📋 当前所有 Topics:"
  echo "========================================"
  docker exec ${KAFKA_CONTAINER} /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --list
  
  echo ""
  echo "✅ Kafka Topics 初始化完成"

# 方案2: 如果是远程 Kafka（需要 kafka-python）
else
  echo "⚠️  本地未找到 Kafka 容器: ${KAFKA_CONTAINER}"
  echo ""
  echo "请在 Kafka 服务器 (${KAFKA_HOST}) 上手动创建 Topics："
  echo ""
  for TOPIC in "${TOPICS[@]}"; do
    echo "docker exec lemo-kafka /opt/kafka/bin/kafka-topics.sh \\"
    echo "  --bootstrap-server localhost:9092 \\"
    echo "  --create \\"
    echo "  --if-not-exists \\"
    echo "  --topic ${TOPIC} \\"
    echo "  --partitions 3 \\"
    echo "  --replication-factor 1"
    echo ""
  done
  
  echo "或者使用 kafka-topics 命令行工具："
  echo ""
  for TOPIC in "${TOPICS[@]}"; do
    echo "kafka-topics.sh --bootstrap-server ${KAFKA_HOST}:${KAFKA_PORT} \\"
    echo "  --create --if-not-exists --topic ${TOPIC} --partitions 3 --replication-factor 1"
    echo ""
  done
fi

echo ""
echo "========================================"
echo "完成"
echo "========================================"

