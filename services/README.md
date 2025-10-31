# 服务启动入口说明

## 📁 目录结构

```
services/
├── recommender/       # HTTP + gRPC 服务（推荐系统主服务）
│   ├── main_http.py   # HTTP 服务启动入口
│   └── main_grpc.py   # gRPC 服务启动入口
├── worker/            # Celery Worker 服务
│   └── main.py        # Worker 启动入口
├── beat/              # Celery Beat 服务（定时任务调度）
│   └── main.py        # Beat 启动入口
└── consumer/          # Kafka Consumer 服务（物品数据消费）
    └── main.py        # Consumer 启动入口
```

## 🚀 服务启动方式

### 1. Recommender 服务（HTTP）

```bash
# 启动 HTTP 服务
python services/recommender/main_http.py

# 或使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 18081
```

### 2. Recommender 服务（gRPC）

```bash
# 启动 gRPC 服务
python services/recommender/main_grpc.py

# 或使用原始脚本
python scripts/run_grpc_server.py
```

### 3. Worker 服务（Celery Worker）

```bash
# 启动 Celery Worker
celery -A app.tasks.celery_app worker -l info -c 4 -Q default,model_training,item_processing,user_profile

# 或使用启动脚本（仅用于开发测试）
python services/worker/main.py
```

### 4. Beat 服务（Celery Beat）

```bash
# 启动 Celery Beat
celery -A app.tasks.celery_app beat -l info --scheduler redbeat.RedBeatScheduler

# 或使用启动脚本（仅用于开发测试）
python services/beat/main.py
```

### 5. Consumer 服务（Kafka Consumer）

```bash
# 启动 Kafka Consumer
python services/consumer/main.py

# 或使用原始脚本
python scripts/run_item_consumer.py
```

## 📋 K8s 部署配置

### HTTP 服务
- **Deployment**: `k8s-deploy/k8s-deployment-http-grpc.yaml`（HTTP 部分）
- **启动命令**: `uvicorn app.main:app --host 0.0.0.0 --port 8080`
- **端口**: `8080`

### gRPC 服务
- **Deployment**: `k8s-deploy/k8s-deployment-http-grpc.yaml`（gRPC 部分）
- **启动命令**: `python scripts/run_grpc_server.py`
- **端口**: `50051`

### Worker 服务
- **Deployment**: `k8s-deploy/k8s-deployment-worker.yaml`
- **启动命令**: `celery -A app.tasks.celery_app worker -l info -c 4`

### Beat 服务
- **Deployment**: `k8s-deploy/k8s-deployment-beat.yaml`
- **启动命令**: `celery -A app.tasks.celery_app beat -l info --scheduler redbeat.RedBeatScheduler`

### Consumer 服务
- **Deployment**: `k8s-deploy/k8s-deployment-consumer.yaml`
- **启动命令**: `python scripts/run_item_consumer.py`

## 🔧 服务隔离说明

### 共享代码（`app/` 目录）
- `app/core/` - 核心配置、数据库连接等
- `app/models/` - 数据模型
- `app/utils/` - 工具函数
- `app/services/` - 业务服务（所有服务共享）

### 服务特定代码
- **Recommender**: `app/api/v1/`（HTTP API）、`app/grpc_server/`（gRPC 服务）
- **Worker**: `app/tasks/`（Celery 任务）
- **Beat**: `app/tasks/celery_app.py`（定时任务配置）
- **Consumer**: `app/services/item/kafka_consumer.py`（消息处理器）

## 📝 注意事项

1. **服务启动入口统一在 `services/` 目录**，便于区分和管理
2. **K8s 部署使用原始命令**，不依赖 `services/` 目录的启动脚本
3. **所有服务共享 `app/` 目录的代码**，但业务逻辑按服务隔离
4. **HTTP 和 gRPC 服务在同一容器中**，可以通过不同端口访问

## 🔄 后续优化建议

1. 考虑将 `app/` 目录中的服务特定代码移到对应的 `services/` 目录
2. 创建统一的服务管理器，支持服务发现和负载均衡
3. 添加服务健康检查和自动重启机制

