# K3s 部署指南

本目录包含推荐系统所有服务的 K3s 部署脚本和配置文件。

## 📁 文件清单

### 部署脚本

| 脚本 | 说明 | 部署服务 |
|------|------|---------|
| `deploy-http-grpc-service.sh` | 部署核心双服务（HTTP + gRPC）| ✅ HTTP API<br/>✅ gRPC |
| `deploy-worker-service.sh` | 部署 Celery Worker 服务 | ✅ Worker |
| `deploy-beat-service.sh` | 部署 Celery Beat 服务 | ✅ Beat |
| `deploy-consumer-service.sh` | 部署 Kafka Consumer 服务 | ✅ Consumer |

### K8s 配置文件

| 配置文件 | 说明 |
|---------|------|
| `k8s-deployment-http-grpc.yaml` | HTTP API + gRPC 服务配置 |
| `k8s-deployment-worker.yaml` | Celery Worker 服务配置（2副本）|
| `k8s-deployment-beat.yaml` | Celery Beat 服务配置（1副本）|
| `k8s-deployment-consumer.yaml` | Kafka Consumer 服务配置 |
| `k3s-jd-config.yaml` | K3s 集群配置文件 |

---

## 🚀 快速开始

### 方案1：部署核心服务（推荐）⭐

**适用场景**：基础功能验证、API 服务

```bash
# 部署 HTTP API + gRPC
cd /Users/edy/PycharmProjects/lemo_recommender
./k8s-deploy/deploy-http-grpc-service.sh
```

**部署结果**：
- ✅ HTTP API（端口 10071，NodePort: 30801）
- ✅ gRPC 服务（端口 10072，ClusterIP）

**访问地址**：
- HTTP API: `http://<K3S_NODE_IP>:30801/api/v1/docs`
- Metrics: `http://<K3S_NODE_IP>:30802/metrics`

---

### 方案2：按需部署服务

**适用场景**：生产环境、需要模型训练和 Kafka 消费

```bash
# 1. 先部署核心服务
cd /Users/edy/PycharmProjects/lemo_recommender
./k8s-deploy/deploy-http-grpc-service.sh

# 2. 需要模型训练时，部署 Worker + Beat
./k8s-deploy/deploy-worker-service.sh
./k8s-deploy/deploy-beat-service.sh

# 3. 需要 Kafka 物品接入时，部署 Consumer
./k8s-deploy/deploy-consumer-service.sh
```

**完整系统部署结果**：
- ✅ HTTP API（端口 10071）
- ✅ gRPC 服务（端口 10072）
- ✅ Celery Worker（支持模型训练）
- ✅ Celery Beat（定时任务调度）
- ✅ Kafka Consumer（消费物品事件）

---

## 📊 服务架构

### 当前部署架构（方案1）

```
┌─────────────────────────────────────────────────────┐
│                   K3s Cluster                        │
│                                                      │
│  ┌──────────────────────┐  ┌──────────────────────┐ │
│  │  HTTP API Service    │  │   gRPC Service       │ │
│  │  Port: 10071         │  │   Port: 10072        │ │
│  │  NodePort: 30801     │  │   ClusterIP          │ │
│  └──────────────────────┘  └──────────────────────┘ │
│           │                          │               │
└───────────┼──────────────────────────┼───────────────┘
            │                          │
            ▼                          ▼
    ┌──────────────────────────────────────────┐
    │         外部依赖服务                       │
    │  • MongoDB (111.228.39.41:27017)        │
    │  • Redis (111.228.39.41:6379)           │
    │  • Kafka (111.228.39.41:9092)           │
    │  • Milvus (111.228.39.41:19530)         │
    └──────────────────────────────────────────┘
```

### 完整架构（方案2）

```
┌─────────────────────────────────────────────────────────────────┐
│                          K3s Cluster                             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  HTTP API    │  │   gRPC       │  │   Celery Worker (×2)   │ │
│  │  Port: 10071 │  │   Port: 10072│  │   Queues: 4            │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
│                                                                  │
│  ┌──────────────┐  ┌────────────────────────────────────────┐  │
│  │ Celery Beat  │  │   Kafka Consumer                        │  │
│  │ (×1)         │  │   Topics: item-events-{tenant_id}      │  │
│  └──────────────┘  └────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 服务管理

### 查看服务状态

```bash
# 查看所有 Pod
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get pods -l app=lemo-service-recommender

# 查看所有 Service
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get svc -l app=lemo-service-recommender

# 查看特定组件
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get pods -l component=http
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get pods -l component=grpc
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get pods -l app=lemo-service-recommender-worker
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get pods -l app=lemo-service-recommender-beat
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get pods -l app=lemo-service-recommender-consumer
```

### 查看日志

```bash
# HTTP API 日志
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev logs -f deployment/lemo-service-recommender-http

# gRPC 日志
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev logs -f deployment/lemo-service-recommender-grpc

# Worker 日志
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev logs -f deployment/lemo-service-recommender-worker

# Beat 日志
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev logs -f deployment/lemo-service-recommender-beat

# Consumer 日志
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev logs -f deployment/lemo-service-recommender-consumer
```

### 扩缩容

```bash
# 扩展 HTTP API 到 3 副本
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev scale deployment lemo-service-recommender-http --replicas=3

# 扩展 Worker 到 4 副本
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev scale deployment lemo-service-recommender-worker --replicas=4
```

### 删除服务

```bash
# 删除所有服务
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete deployment -l app=lemo-service-recommender
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete svc -l app=lemo-service-recommender

# 删除特定服务
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete deployment lemo-service-recommender-http
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete deployment lemo-service-recommender-grpc
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete deployment lemo-service-recommender-worker
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete deployment lemo-service-recommender-beat
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete deployment lemo-service-recommender-consumer
```

---

## 🛠️ 故障排查

### 问题1：Pod 无法启动

```bash
# 查看 Pod 详情
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev describe pod <POD_NAME>

# 查看事件
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get events --sort-by='.lastTimestamp'
```

### 问题2：镜像拉取失败

```bash
# 检查镜像密钥
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get secret regcred

# 重新创建密钥
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete secret regcred
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev create secret docker-registry regcred \
  --docker-server=registry.cn-beijing.aliyuncs.com \
  --docker-username=北京乐莫科技 \
  --docker-password=Andrew1870361
```

### 问题3：服务无法访问

```bash
# 检查 Service
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get svc

# 检查端口映射
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev describe svc lemo-service-recommender-http

# 测试健康检查
curl http://<K3S_NODE_IP>:30801/health
```

### 问题4：Worker 任务不执行

```bash
# 进入 Worker Pod
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev exec -it deployment/lemo-service-recommender-worker -- bash

# 检查 Celery 连接
celery -A app.tasks.celery_app inspect ping

# 查看活跃任务
celery -A app.tasks.celery_app inspect active

# 查看注册的任务
celery -A app.tasks.celery_app inspect registered
```

### 问题5：Consumer 不消费消息

```bash
# 进入 Consumer Pod
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev exec -it deployment/lemo-service-recommender-consumer -- bash

# 检查 Kafka 连接
python3 -c "from kafka import KafkaConsumer; c = KafkaConsumer(bootstrap_servers='111.228.39.41:9092'); print('OK')"

# 查看日志
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev logs -f deployment/lemo-service-recommender-consumer
```

---

## 📝 配置说明

### ConfigMap 配置项

所有服务共享 `lemo-service-recommender-config` ConfigMap：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `ENV` | 运行环境 | `prod` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `MONGODB_URL` | MongoDB 连接地址 | `mongodb://lemo_user:***@111.228.39.41:27017/lemo_recommender` |
| `REDIS_URL` | Redis 连接地址 | `redis://:***@111.228.39.41:6379/0` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka 地址 | `111.228.39.41:9092` |
| `MILVUS_HOST` | Milvus 地址 | `111.228.39.41` |
| `MILVUS_PORT` | Milvus 端口 | `19530` |
| `HTTP_PORT` | HTTP API 端口 | `10071` |
| `GRPC_PORT` | gRPC 端口 | `10072` |

### 资源限制

| 服务 | CPU 请求/限制 | 内存 请求/限制 | 副本数 |
|------|--------------|---------------|--------|
| HTTP API | 100m / 500m | 128Mi / 512Mi | 1 |
| gRPC | 100m / 500m | 128Mi / 512Mi | 1 |
| Worker | 500m / 2000m | 512Mi / 2Gi | 2 |
| Beat | 100m / 200m | 128Mi / 256Mi | 1 |
| Consumer | 250m / 500m | 256Mi / 512Mi | 1 |

**总计**（完整部署）：
- CPU: 2.4 cores（请求）/ 7.9 cores（限制）
- 内存: 1.9Gi（请求）/ 7.0Gi（限制）

---

## 🔗 相关文档

- [服务拆分方案](../docs/服务拆分方案.md) - 详细架构设计
- [系统设计](../docs/系统设计.md) - 整体设计文档
- [物品数据接入指南](../docs/物品数据接入指南.md) - 物品数据接入
- [行为数据埋点指南](../docs/行为数据埋点指南.md) - 行为埋点接入
- [开发指南](../docs/开发指南.md) - 开发和测试指南

---

## 📞 联系方式

如有问题，请联系开发团队或查看项目文档。
