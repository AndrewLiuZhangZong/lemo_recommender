# 在远程 Kafka 服务器上创建 Topics

## 方法1：使用 Docker （推荐）

如果 Kafka 运行在 Docker 中，在 **111.228.39.41** 服务器上执行：

```bash
# 创建 items-ingest Topic
docker exec lemo-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create \
  --if-not-exists \
  --topic items-ingest \
  --partitions 3 \
  --replication-factor 1

# 创建 vlog-items Topic
docker exec lemo-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create \
  --if-not-exists \
  --topic vlog-items \
  --partitions 3 \
  --replication-factor 1

# 创建 news-items Topic
docker exec lemo-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create \
  --if-not-exists \
  --topic news-items \
  --partitions 3 \
  --replication-factor 1

# 列出所有 Topics
docker exec lemo-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --list

# 查看 Topic 详情
docker exec lemo-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --topic items-ingest
```

## 方法2：直接使用 kafka-topics 命令

如果 Kafka 不在 Docker 中：

```bash
# 进入 Kafka 安装目录
cd /opt/kafka  # 或你的 Kafka 安装路径

# 创建 Topics
bin/kafka-topics.sh --bootstrap-server localhost:9092 \
  --create --if-not-exists --topic items-ingest --partitions 3 --replication-factor 1

bin/kafka-topics.sh --bootstrap-server localhost:9092 \
  --create --if-not-exists --topic vlog-items --partitions 3 --replication-factor 1

bin/kafka-topics.sh --bootstrap-server localhost:9092 \
  --create --if-not-exists --topic news-items --partitions 3 --replication-factor 1

# 列出所有 Topics
bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
```

## 方法3：一键脚本

创建一个脚本 `create_topics.sh`：

```bash
#!/bin/bash
TOPICS=("items-ingest" "vlog-items" "news-items")

for TOPIC in "${TOPICS[@]}"; do
  docker exec lemo-kafka /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --create \
    --if-not-exists \
    --topic $TOPIC \
    --partitions 3 \
    --replication-factor 1 \
    && echo "✅ $TOPIC 创建成功" || echo "⚠️  $TOPIC 可能已存在"
done

echo ""
echo "📋 所有 Topics:"
docker exec lemo-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --list
```

运行：
```bash
chmod +x create_topics.sh && ./create_topics.sh
```

## 验证

创建完成后，检查 Consumer 日志是否还有错误：

```bash
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev logs -f deployment/lemo-service-recommender-consumer
```

应该看到类似这样的输出：
```
✅ Kafka Consumer 已连接
✅ 订阅 Topics: ['items-ingest', 'vlog-items', 'news-items']
✅ 等待消息...
```

