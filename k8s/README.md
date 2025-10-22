# Kubernetes 部署配置

## 目录结构

```
k8s/
├── base/                           # 基础资源配置
│   ├── namespace.yaml              # 命名空间
│   ├── configmap.yaml              # 配置文件
│   └── secret.yaml                 # 敏感信息
│
├── services/                       # Service配置
│   ├── scenario-service.yaml
│   ├── item-service.yaml
│   ├── behavior-service.yaml
│   ├── recommendation-service.yaml
│   ├── feature-service.yaml
│   └── model-service.yaml
│
├── deployments/                    # Deployment配置
│   ├── scenario-service.yaml
│   ├── item-service.yaml
│   ├── behavior-service.yaml
│   ├── recommendation-service.yaml
│   ├── feature-service.yaml
│   └── model-service.yaml
│
└── README.md                       # 本文件
```

## 部署顺序

### 1. 基础设施（由运维团队部署）
```bash
# MongoDB, Redis, Kafka需提前部署或使用云服务
```

### 2. 基础资源
```bash
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f k8s/base/secret.yaml
```

### 3. 独立服务（无依赖，可并行部署）
```bash
# 场景管理服务
kubectl apply -f k8s/deployments/scenario-service.yaml
kubectl apply -f k8s/services/scenario-service.yaml

# 物品管理服务
kubectl apply -f k8s/deployments/item-service.yaml
kubectl apply -f k8s/services/item-service.yaml

# 行为采集服务
kubectl apply -f k8s/deployments/behavior-service.yaml
kubectl apply -f k8s/services/behavior-service.yaml

# 特征服务
kubectl apply -f k8s/deployments/feature-service.yaml
kubectl apply -f k8s/services/feature-service.yaml

# 模型服务
kubectl apply -f k8s/deployments/model-service.yaml
kubectl apply -f k8s/services/model-service.yaml
```

### 4. 推荐服务（依赖其他服务）
```bash
kubectl apply -f k8s/deployments/recommendation-service.yaml
kubectl apply -f k8s/services/recommendation-service.yaml
```

## 服务端口分配

| 服务名称 | HTTP端口 | gRPC端口 | 用途 |
|---------|---------|---------|-----|
| scenario-service | 8001 | 9001 | 场景管理 |
| item-service | 8002 | 9002 | 物品管理 |
| behavior-service | 8003 | - | 行为采集 |
| recommendation-service | 8004 | - | 推荐服务 |
| feature-service | - | 9005 | 特征服务（仅gRPC） |
| model-service | - | 9006 | 模型服务（仅gRPC） |

## 健康检查

所有服务提供以下健康检查端点：

- **Liveness**: `/health/live` - 服务是否存活
- **Readiness**: `/health/ready` - 服务是否就绪

## 环境变量

通过ConfigMap和Secret管理：

```yaml
# ConfigMap: 非敏感配置
- MONGODB_URL
- REDIS_URL
- KAFKA_BOOTSTRAP_SERVERS
- SERVICE_URLS (其他服务地址)

# Secret: 敏感信息
- MONGODB_PASSWORD
- REDIS_PASSWORD
- SECRET_KEY
```

## 监控与日志

- **Metrics**: Prometheus自动采集 `/metrics` 端点
- **Logging**: 日志输出到stdout，由K8s收集
- **Tracing**: 集成Jaeger (可选)

## 扩缩容

```bash
# 水平扩容
kubectl scale deployment recommendation-service --replicas=5 -n lemo-recommender

# 自动扩缩容（HPA）
kubectl autoscale deployment recommendation-service \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n lemo-recommender
```

## 滚动更新

```bash
# 更新镜像
kubectl set image deployment/recommendation-service \
  recommendation-service=lemo-recommender/recommendation-service:v2.0 \
  -n lemo-recommender

# 查看滚动状态
kubectl rollout status deployment/recommendation-service -n lemo-recommender

# 回滚
kubectl rollout undo deployment/recommendation-service -n lemo-recommender
```

