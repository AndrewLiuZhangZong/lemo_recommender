# 服务启动入口说明（v2.0 - 13个服务）

> 📌 本文档说明推荐系统v2.0的完整服务拆分和启动方式

---

## 🎯 v2.0 完整架构（13个服务）

```
services/
├── 在线服务层（6个服务）
│   ├── recall/              # 召回服务
│   ├── ranking/             # 精排服务
│   ├── reranking/           # 重排服务
│   ├── user/                # 用户服务
│   ├── item/                # 物品服务
│   └── behavior/            # 行为服务
│
├── 离线计算层（4个服务）
│   ├── model-training/      # 模型训练服务
│   ├── feature-engineering/ # 特征工程服务
│   ├── vector-generation/   # 向量生成服务
│   └── worker/              # 数据同步服务（Worker队列）
│
└── 实时计算层（3个服务）
    ├── flink-realtime/      # Flink实时特征服务
    ├── beat/                # Beat定时任务调度
    └── consumer/            # Kafka消费服务

额外服务（编排层）:
├── recommender/             # HTTP + gRPC 服务（BFF编排层）
```

---

## 📋 服务列表详情

### 在线服务层

| 服务 | 端口 | 说明 | 状态 | 优先级 |
|------|------|------|------|--------|
| **recall** | 8081 | 多路召回（ALS/CF/Hot） | ✅ 已实现 | P0 |
| **ranking** | 8082 | 精排（DeepFM/模型推理） | ✅ 已实现 | P0 |
| **reranking** | 8083 | 重排（多样性/新鲜度） | ✅ 已实现 | P0 |
| **user** | 8084 | 用户画像查询 | 🆕 待实现 | P1 |
| **item** | 8085 | 物品元数据查询 | 🆕 待实现 | P1 |
| **behavior** | 8086 | 行为埋点采集 | 🆕 待实现 | P1 |

### 离线计算层

| 服务 | 端口 | 说明 | 状态 | 优先级 |
|------|------|------|------|--------|
| **model-training** | 8091 | 模型训练（GPU） | 🆕 待实现 | P2 |
| **feature-engineering** | 8092 | 特征计算（Spark/Flink） | 🆕 待实现 | P2 |
| **vector-generation** | 8093 | 向量生成（Embedding） | 🆕 待实现 | P2 |
| **worker** | - | Celery异步任务 | ✅ 已实现 | P0 |

### 实时计算层

| 服务 | 端口 | 说明 | 状态 | 优先级 |
|------|------|------|------|--------|
| **flink-realtime** | 8094 | Flink实时特征 | 🆕 待实现 | P2 |
| **beat** | - | Celery定时任务 | ✅ 已实现 | P0 |
| **consumer** | - | Kafka物品消费 | ✅ 已实现 | P1 |

### 编排层

| 服务 | 端口 | 说明 | 状态 | 优先级 |
|------|------|------|------|--------|
| **recommender** | 10071/10072 | HTTP+gRPC（BFF编排） | ✅ 已实现 | P0 |

---

## 🚀 启动方式

### Phase 1: 核心推荐服务（已实现 ✅）

```bash
# 1. 召回服务
python services/recall/main.py
# 端口: 8081

# 2. 精排服务
python services/ranking/main.py
# 端口: 8082

# 3. 重排服务
python services/reranking/main.py
# 端口: 8083

# 4. HTTP API（BFF编排层）
python services/recommender/main_http.py
# 端口: 10071

# 5. Worker
python services/worker/main.py

# 6. Beat
python services/beat/main.py
```

---

### Phase 2: 数据服务（待实现 🆕）

```bash
# 1. 用户服务
python services/user/main.py
# 端口: 8084

# 2. 物品服务
python services/item/main.py
# 端口: 8085

# 3. 行为服务
python services/behavior/main.py
# 端口: 8086

# 4. Kafka Consumer
python services/consumer/main.py
```

---

### Phase 3: 计算服务（待实现 🆕）

```bash
# 1. 模型训练服务
python services/model-training/main.py
# 端口: 8091

# 2. 特征工程服务
python services/feature-engineering/main.py
# 端口: 8092

# 3. 向量生成服务
python services/vector-generation/main.py
# 端口: 8093

# 4. Flink实时服务
python services/flink-realtime/main.py
# 端口: 8094
```

---

## ☸️ K8s部署

### 一键部署所有服务

```bash
# Phase 1: 核心推荐服务
./k8s-deploy/deploy-all-microservices.sh

# Phase 2: 数据服务（即将支持）
./k8s-deploy/deploy-data-services.sh

# Phase 3: 计算服务（即将支持）
./k8s-deploy/deploy-compute-services.sh
```

### 单独部署

```bash
# 在线服务
./k8s-deploy/deploy-recall-service.sh
./k8s-deploy/deploy-ranking-service.sh
./k8s-deploy/deploy-reranking-service.sh
./k8s-deploy/deploy-user-service.sh         # 🆕
./k8s-deploy/deploy-item-service.sh         # 🆕
./k8s-deploy/deploy-behavior-service.sh     # 🆕

# 离线服务
./k8s-deploy/deploy-model-training.sh       # 🆕
./k8s-deploy/deploy-feature-engineering.sh  # 🆕
./k8s-deploy/deploy-vector-generation.sh    # 🆕

# 实时服务
./k8s-deploy/deploy-flink-realtime.sh       # 🆕

# 编排层
./k8s-deploy/deploy-http-grpc-service.sh

# Worker & Beat & Consumer
./k8s-deploy/deploy-worker-service.sh
./k8s-deploy/deploy-beat-service.sh
./k8s-deploy/deploy-consumer-service.sh
```

---

## 📊 服务依赖关系

```
外部请求
    ↓
recommender (BFF编排层)
    ↓
    ├─→ user-service (用户画像)
    ├─→ item-service (物品信息)
    └─→ recall-service (召回)
            ↓
        ranking-service (精排)
            ↓
        reranking-service (重排)
            ↓
        返回结果

后台任务:
    ├─→ behavior-service → Kafka → consumer
    ├─→ model-training → 训练模型
    ├─→ feature-engineering → 特征计算
    ├─→ vector-generation → 向量生成
    ├─→ flink-realtime → 实时特征
    └─→ worker + beat → 定时任务
```

---

## 📦 测试环境资源配置

**总资源**: 2CPU + 8G内存

### Phase 1（当前）: 7个服务

| 服务 | 副本 | CPU | 内存 |
|------|------|-----|------|
| recall | 1 | 200m | 512Mi |
| ranking | 1 | 200m | 512Mi |
| reranking | 1 | 100m | 256Mi |
| recommender | 1 | 100m | 128Mi |
| worker | 1 | 200m | 256Mi |
| beat | 1 | 100m | 128Mi |
| consumer | 1 | 250m | 256Mi |
| **合计** | **7** | **1.15核** | **2.05Gi** |

✅ **资源利用率**: 57.5% CPU, 25.6% 内存

---

### Phase 2（扩展）: 10个服务

在Phase 1基础上增加：

| 服务 | 副本 | CPU | 内存 |
|------|------|-----|------|
| user | 1 | 150m | 256Mi |
| item | 1 | 150m | 256Mi |
| behavior | 1 | 150m | 256Mi |
| **新增合计** | **3** | **450m** | **768Mi** |
| **总计** | **10** | **1.6核** | **2.8Gi** |

✅ **资源利用率**: 80% CPU, 35% 内存

---

### Phase 3（完整）: 13个服务

在Phase 2基础上增加：

| 服务 | 副本 | CPU | 内存 | 说明 |
|------|------|-----|------|------|
| model-training | 0-1 | 2000m | 2Gi | 按需启动 |
| feature-engineering | 0-1 | 500m | 1Gi | 按需启动 |
| vector-generation | 0-1 | 300m | 512Mi | 按需启动 |
| flink-realtime | 0-1 | 500m | 1Gi | 按需启动 |

⚠️ **说明**: 计算服务在测试环境按需启动，不常驻运行

---

## 🎯 实施路线图

### ✅ Phase 1（已完成）

- ✅ 召回服务
- ✅ 精排服务
- ✅ 重排服务
- ✅ Worker/Beat/Consumer
- ✅ Recommender（BFF）

**状态**: 已部署，可测试

---

### 🚧 Phase 2（进行中）

- 🆕 用户服务
- 🆕 物品服务
- 🆕 行为服务

**预计**: 1-2周

---

### 📅 Phase 3（规划中）

- 🆕 模型训练服务
- 🆕 特征工程服务
- 🆕 向量生成服务
- 🆕 Flink实时服务

**预计**: 3-4周

---

## 📖 相关文档

- 📋 [系统优化计划v2.0](../docs/系统优化计划v2.0.md) - 完整架构设计
- 📝 [测试环境部署指南](../docs/测试环境部署指南.md) - 2CPU+8G部署说明
- 🚀 [系统优化计划v1.0](../docs/系统优化计划v1.0.md) - 性能优化基础

---

**版本**: v2.0  
**更新日期**: 2024-11-05  
**服务数**: 13个（当前实现7个）  
**适用规模**: 测试环境（2CPU+8G）→ 生产环境（2亿+用户）
