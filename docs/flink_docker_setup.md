# Flink Docker 安装指南

## 概述

Flink 可以通过 Docker 安装，支持两种模式：

1. **Standalone 模式**（单机）：适合开发/测试环境
2. **集群模式**（多容器）：适合生产环境

当前配置使用 **Standalone 模式**（单个容器包含 JobManager 和 TaskManager）。

## 重要说明

**JobManager 和 TaskManager 维护者：**
- ✅ 维护者：Flink 官方（Apache Flink）
- 📦 来源：Flink Docker 镜像（`flink:1.19-scala_2.12-java11`）
- 🚀 启动：通过 `start-cluster.sh` 自动启动
- 🔗 我们的服务：只负责通过 REST API 与 Flink 集群通信（不维护 JobManager/TaskManager）

## 快速开始

### 1. 启动 Flink

```bash
# 启动所有服务（包括 Flink）
docker-compose up -d

# 或者只启动 Flink
docker-compose up -d flink
```

### 2. 访问 Flink Web UI

- **地址**: http://localhost:8081
- **默认显示**: Flink 集群概览、作业列表、TaskManager 状态等

### 3. 验证安装

```bash
# 检查 Flink 是否运行
docker-compose ps flink

# 查看 Flink 日志
docker-compose logs -f flink

# 测试 REST API
curl http://localhost:8081/overview
```

## 配置说明

### 端口映射

- `8081`: Flink Web UI（Dashboard）
- `6123`: JobManager RPC（内部通信）

### 环境变量

- `FLINK_PROPERTIES`: Flink 配置文件内容
  - `jobmanager.rpc.address`: JobManager 地址（容器内使用服务名 `flink`）
  - `taskmanager.numberOfTaskSlots`: TaskManager 任务槽数量（默认 4）
  - `parallelism.default`: 默认并行度（默认 2）

### 数据卷

- `flink_data`: Flink 数据目录
- `flink_checkpoints`: Checkpoint 存储目录
- `flink_savepoints`: Savepoint 存储目录

## 生产环境配置

如果需要更高可用性和性能，可以使用集群模式：

### 方式 1: Docker Compose 多容器集群

创建 `docker-compose-flink-cluster.yml`:

```yaml
version: '3.8'

services:
  # JobManager
  flink-jobmanager:
    image: flink:1.19-scala_2.12-java11
    container_name: flink-jobmanager
    ports:
      - "8081:8081"
    environment:
      FLINK_PROPERTIES: |
        jobmanager.rpc.address: flink-jobmanager
    command: jobmanager
    volumes:
      - flink_checkpoints:/opt/flink/checkpoints
    networks:
      - flink-network

  # TaskManager
  flink-taskmanager:
    image: flink:1.19-scala_2.12-java11
    container_name: flink-taskmanager
    environment:
      FLINK_PROPERTIES: |
        jobmanager.rpc.address: flink-jobmanager
        taskmanager.numberOfTaskSlots: 4
    command: taskmanager
    depends_on:
      - flink-jobmanager
    volumes:
      - flink_checkpoints:/opt/flink/checkpoints
    networks:
      - flink-network

networks:
  flink-network:
    driver: bridge

volumes:
  flink_checkpoints:
```

### 方式 2: Kubernetes 部署

参考官方文档：https://nightlies.apache.org/flink/flink-docs-stable/docs/deployment/resource-providers/native_kubernetes/

## 配置应用连接 Flink

### 环境变量

在 `.env` 或 `config/local.env` 中配置：

```bash
# Flink 集群配置
FLINK_REST_URL=http://localhost:8081
FLINK_REST_TIMEOUT=30
```

### 网络配置

如果应用也在 Docker 容器中运行，使用服务名：

```bash
FLINK_REST_URL=http://flink:8081
```

## 常用操作

### 提交作业

```bash
# 提交 JAR 作业
docker exec lemo-flink bin/flink run \
  /path/to/your-job.jar \
  --class com.example.YourMainClass

# 提交 PyFlink 作业
docker exec lemo-flink bin/flink run \
  -py /path/to/your-job.py
```

### 查看作业列表

```bash
# 通过 REST API
curl http://localhost:8081/jobs

# 通过命令行
docker exec lemo-flink bin/flink list
```

### 停止作业

```bash
# 通过 REST API
curl -X POST http://localhost:8081/jobs/{job-id}/stop

# 通过命令行
docker exec lemo-flink bin/flink cancel {job-id}
```

## 故障排查

### 检查 Flink 状态

```bash
# 查看容器状态
docker-compose ps flink

# 查看日志
docker-compose logs flink

# 进入容器检查
docker exec -it lemo-flink bash
```

### 常见问题

1. **端口冲突**: 如果 8081 端口被占用，修改 `docker-compose.yml` 中的端口映射
2. **内存不足**: 调整 `taskmanager.memory.process.size` 配置
3. **网络问题**: 确保容器在同一个网络中（`lemo-network`）

## 参考资源

- Flink 官方文档: https://nightlies.apache.org/flink/flink-docs-stable/
- Docker Hub Flink: https://hub.docker.com/_/flink
- Flink Docker 镜像: https://github.com/apache/flink-docker

