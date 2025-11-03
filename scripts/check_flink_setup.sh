#!/bin/bash

echo "=========================================="
echo "Flink 环境检查脚本"
echo "=========================================="
echo ""

# 1. 查找 Flink 容器
echo "1. 查找 Flink 容器:"
docker ps | grep -i flink
echo ""

# 2. 获取 Flink 容器名称
FLINK_CONTAINER=$(docker ps --format '{{.Names}}' | grep -i flink | head -1)

if [ -z "$FLINK_CONTAINER" ]; then
    echo "错误: 未找到运行中的 Flink 容器"
    echo ""
    echo "请检查 docker-compose.yml 并启动 Flink:"
    echo "  cd /www/wwwroot/dockerfiles"
    echo "  docker-compose up -d flink"
    exit 1
fi

echo "2. 找到 Flink 容器: $FLINK_CONTAINER"
echo ""

# 3. 检查 /opt/flink/opt/ 目录
echo "3. 检查 /opt/flink/opt/ 目录内容:"
docker exec $FLINK_CONTAINER ls -lh /opt/flink/opt/
echo ""

# 4. 查找 Kafka connector
echo "4. 查找 Kafka connector:"
KAFKA_JARS=$(docker exec $FLINK_CONTAINER ls /opt/flink/opt/ 2>/dev/null | grep -i kafka || echo "未找到")
if [ "$KAFKA_JARS" = "未找到" ]; then
    echo "❌ 未找到 Kafka connector JAR"
    echo ""
    echo "需要下载 Kafka connector JAR 文件"
    echo "请执行以下命令:"
    echo ""
    echo "docker exec $FLINK_CONTAINER bash -c 'cd /opt/flink/opt && wget https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.1.0-1.19/flink-sql-connector-kafka-3.1.0-1.19.jar'"
else
    echo "✓ 找到 Kafka connector:"
    echo "$KAFKA_JARS"
    echo ""
    echo "完整路径:"
    for jar in $KAFKA_JARS; do
        echo "  /opt/flink/opt/$jar"
    done
fi
echo ""

# 5. 检查 /opt/flink/lib/ 目录（自动加载的 JAR）
echo "5. 检查 /opt/flink/lib/ 目录:"
docker exec $FLINK_CONTAINER ls /opt/flink/lib/ | grep -i kafka || echo "lib 目录中没有 Kafka connector"
echo ""

# 6. 检查 Python 环境
echo "6. 检查 Python 和 PyFlink:"
docker exec $FLINK_CONTAINER python3 --version
docker exec $FLINK_CONTAINER python3 -c "import pyflink; print(f'PyFlink version: {pyflink.__version__}')" 2>/dev/null || echo "PyFlink 未安装或版本信息不可用"
echo ""

# 7. 检查 Flink 版本
echo "7. Flink 版本:"
docker exec $FLINK_CONTAINER /opt/flink/bin/flink --version
echo ""

echo "=========================================="
echo "检查完成"
echo "=========================================="

