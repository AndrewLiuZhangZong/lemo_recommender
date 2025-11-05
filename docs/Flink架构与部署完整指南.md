# Flink 实时特征计算 - 架构与部署指南（v2.0）

> **v2.0架构说明**：Flink作为固定的实时特征计算服务，采用Kubernetes Operator + Application Mode部署

## 📖 目录

1. [Flink在推荐系统中的作用](#flink在推荐系统中的作用)
2. [v2.0架构变化](#v2.0架构变化)
3. [核心组件](#核心组件)
4. [部署步骤](#部署步骤)
5. [Flink作业说明](#flink作业说明)
6. [运维管理](#运维管理)
7. [故障排查](#故障排查)
8. [高级功能：动态作业提交](#高级功能动态作业提交)

---

## 🎯 Flink在推荐系统中的作用

### 核心职责

Flink是推荐系统的**实时特征计算引擎**，7×24小时运行，处理4类核心任务：

| 任务 | 输入 | 输出 | 用途 |
|------|------|------|------|
| **用户实时特征** | Kafka用户行为 | MongoDB/Redis | 近1小时观看/点赞数，活跃时段 |
| **物品热度计算** | Kafka用户行为 | Redis ZSET | Top 1000热门物品（召回使用） |
| **推荐指标统计** | Kafka用户行为 | Prometheus | CTR、观看时长、完播率（监控） |
| **行为数据ETL** | Kafka用户行为 | ClickHouse | 实时写入OLAP（离线训练） |

### 数据流

```
用户行为（点击/观看/点赞）
  ↓
Behavior Service → Kafka (user_behaviors topic)
  ↓
Flink实时计算（窗口聚合）
  ↓
  ├─→ Redis（实时特征，供Recall/Ranking使用）
  ├─→ MongoDB（用户画像，持久化）
  ├─→ Prometheus（监控指标，运营大盘）
  └─→ ClickHouse（行为明细，离线训练）
```

---

## 🔄 v2.0架构变化

### 旧架构（已废弃）❌

- ❌ 后台管理界面动态创建作业模板
- ❌ 前端提交作业请求到HTTP API
- ❌ Python后端动态生成FlinkDeployment YAML
- ❌ 每个任务一个独立的FlinkDeployment

**问题**：管理复杂、资源碎片化、不适合持续运行的实时服务

### 新架构（v2.0）✅

- ✅ **固定部署**：Flink作为独立微服务静态部署
- ✅ **统一管理**：一个FlinkDeployment运行所有实时任务
- ✅ **配置驱动**：从K8s ConfigMap读取配置，无需重启
- ✅ **持续运行**：7×24小时运行，Flink Operator自动故障恢复

**部署方式**：
```bash
kubectl apply -f k8s-deploy/flink-deployment-realtime-service.yaml
```

---

## 🏗️ 架构概述

### 设计理念

v2.0采用 **Flink Kubernetes Operator + Application Mode + 固定部署** 架构，这是业界标准的云原生实时计算方案，被阿里云、字节跳动、美团等公司广泛使用。

### 核心优势

| 特性 | 传统 Session 模式 | Operator Application 模式 ✅ |
|------|------------------|----------------------------|
| **资源隔离** | ❌ 共享集群 | ✅ 每个作业独立集群 |
| **故障隔离** | ❌ 一个作业失败影响其他作业 | ✅ 作业间完全隔离 |
| **资源利用** | ❌ 需预留资源 | ✅ 按需分配，自动扩缩容 |
| **运维管理** | ❌ 手动管理生命周期 | ✅ Operator 自动管理 |
| **多租户支持** | ❌ 资源争抢 | ✅ 完全隔离 |
| **部署复杂度** | 🟡 中等 | 🟢 简单（声明式） |

---

## 🧩 核心组件

### 组件关系图

```
┌─────────────────────────────────────────────────────────────────┐
│                         服务器2 (K8s 集群)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Namespace: flink-operator-system              │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │  Flink Kubernetes Operator (Pod)                     │ │  │
│  │  │  - 监听 FlinkDeployment CRD                          │ │  │
│  │  │  - 自动创建/管理 JobManager & TaskManager            │ │  │
│  │  │  - 处理故障恢复、扩缩容                               │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  Namespace: lemo-dev                       │  │
│  │  ┌────────────────────────────────────────────────────┐   │  │
│  │  │  推荐服务 (HTTP/gRPC/Worker/Beat/Consumer)          │   │  │
│  │  │  - 创建 FlinkDeployment CRD                         │   │  │
│  │  │  - 查询作业状态                                      │   │  │
│  │  └────────────────────────────────────────────────────┘   │  │
│  │                                                             │  │
│  │  ┌────────────────────────────────────────────────────┐   │  │
│  │  │  FlinkDeployment: job-example-py (CRD)             │   │  │
│  │  │    ├─ JobManager Pod                               │   │  │
│  │  │    │   - 调度和协调                                 │   │  │
│  │  │    │   - REST API (8081)                           │   │  │
│  │  │    └─ TaskManager Pod(s)                           │   │  │
│  │  │        - 执行任务                                   │   │  │
│  │  │        - 运行 Python 脚本                           │   │  │
│  │  └────────────────────────────────────────────────────┘   │  │
│  │                                                             │  │
│  │  ┌────────────────────────────────────────────────────┐   │  │
│  │  │  FlinkDeployment: job-example-jar (CRD)            │   │  │
│  │  │    ├─ JobManager Pod                               │   │  │
│  │  │    └─ TaskManager Pod(s)                           │   │  │
│  │  └────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 组件说明

#### 1. **Flink Kubernetes Operator**
- **位置**: `flink-operator-system` namespace
- **职责**:
  - 监听 `FlinkDeployment` 自定义资源（CRD）
  - 自动创建和管理 Flink 集群（JobManager + TaskManager）
  - 处理作业的生命周期（启动、停止、重启、扩缩容）
  - 管理 Checkpoint、Savepoint
  - 故障自动恢复

#### 2. **FlinkDeployment CRD**
- **定义**: Kubernetes 自定义资源，声明式描述 Flink 作业
- **内容**:
  - 镜像配置
  - 资源配置（CPU、内存）
  - 作业参数（脚本 URL、并行度等）
  - Flink 配置（checkpoint、状态后端等）

#### 3. **JobManager Pod**
- **每个作业一个**，负责：
  - 作业调度和协调
  - Checkpoint 协调
  - 故障恢复
  - REST API 服务（端口 8081）

#### 4. **TaskManager Pod(s)**
- **可多个**，负责：
  - 执行具体的任务
  - 运行用户代码（Python 脚本、JAR 等）
  - 管理状态数据

#### 5. **推荐服务**
- **位置**: `lemo-dev` namespace
- **职责**:
  - 接收用户提交的作业请求
  - 生成 `FlinkDeployment` YAML
  - 通过 K8s API 创建 CRD
  - 查询作业状态（通过 K8s API）

---

## 🌐 部署架构

### 服务器规划

| 服务器 | IP | 用途 | 组件 |
|--------|-----|------|------|
| **服务器1** | `111.228.39.41` | ~~Flink Session 集群~~（已停用） | - |
| **服务器2** | `117.72.196.41` | K8s 集群 (K3s) | Operator、推荐服务、Flink 作业 |

### 网络架构

```
用户/前端
   │
   ├─> HTTP API ──> 推荐服务 (K8s Service)
   │                   │
   │                   ├─> K8s API Server
   │                   │   └─> 创建 FlinkDeployment CRD
   │                   │
   │                   └─> 查询作业状态
   │
   └─> 外部依赖:
       ├─> MongoDB: 111.228.39.41:27017
       ├─> Redis: 111.228.39.41:6379
       ├─> Kafka: 111.228.39.41:9092
       └─> (Flink 作业通过 K8s Service 访问这些依赖)
```

---

## 🚀 部署步骤

### 前提条件

1. ✅ K8s 集群已部署 (K3s)
2. ✅ kubectl 已配置
3. ✅ Helm 已安装（可选，推荐）
4. ✅ Docker 本地环境可构建镜像
5. ✅ ACR 镜像仓库可访问

### 步骤1: 准备 kubeconfig

```bash
# 在服务器2上
cp /etc/rancher/k3s/k3s.yaml /root/k3s-jd-config.yaml

# 修改 server 地址为外网 IP
vi /root/k3s-jd-config.yaml
# 将 server: https://127.0.0.1:6443
# 改为 server: https://117.72.196.41:6443

# 或者在本地 Mac 上
# 将 k3s-jd-config.yaml 放到项目的 k8s-deploy/ 目录
```

### 步骤2: 安装 Flink Kubernetes Operator

**在本地 Mac 或服务器2上执行：**

```bash
# 方式A: 在项目目录中执行
cd /path/to/lemo_recommender
bash scripts/install_flink_operator.sh

# 方式B: 远程执行（在服务器2上）
ssh root@117.72.196.41
cd /root/lemo_recommender
bash scripts/install_flink_operator.sh
```

**脚本会自动：**
1. 检测 kubeconfig 路径
2. 安装 cert-manager（Operator 依赖）
3. 安装 Flink Kubernetes Operator
4. 验证安装状态

**预期输出：**
```
========================================
✓ Flink Kubernetes Operator 安装成功！
========================================

验证命令：
  kubectl get pods -n flink-operator-system
  kubectl get crd | grep flink
```

### 步骤3: 验证 Operator 安装

```bash
export KUBECONFIG=/root/k3s-jd-config.yaml

# 查看 Operator Pod
kubectl get pods -n flink-operator-system
# 输出：
# NAME                                         READY   STATUS    RESTARTS   AGE
# flink-kubernetes-operator-xxx                1/1     Running   0          5m

# 查看 CRD
kubectl get crd | grep flink
# 输出：
# flinkdeployments.flink.apache.org     2025-11-03T05:33:54Z
# flinksessionjobs.flink.apache.org     2025-11-03T05:33:55Z
```

### 步骤4: 构建并推送 Flink 镜像

#### 4.1 镜像架构说明

我们采用**两层镜像架构**，符合业界最佳实践（阿里云、字节跳动等大厂标准）：

```
flink:2.0-scala_2.12-java11 (官方基础镜像 - 最新版)
  ↓
flink-python:latest (添加 Python 3.11 + PyFlink 2.1.1 + 依赖库)
  ↓  
flink-app:latest (添加 entrypoint.py 脚本下载器)
```

**镜像说明**：

| 镜像 | 基础镜像 | 新增内容 | 用途 |
|------|---------|---------|------|
| `flink:2.0` | - | Flink 官方镜像（最新版） | 提供 Flink 运行时（Java） |
| `flink-python:latest` | `flink:2.0` | Python 3.11 + **apache-flink==2.1.1** + 依赖库 | 提供 PyFlink API |
| `flink-app:latest` | `flink-python:latest` | `entrypoint.py` 脚本下载器 | 提供作业入口点 |

**版本说明**（使用最新稳定版本）：
- 🆕 **Flink 2.0.0**（2025-10-02 发布）
- 🆕 **PyFlink 2.1.1**（2025-10-28 发布）
- 🆕 **Kafka Connector 3.3.0-2.0**（匹配 Flink 2.0）

**关键点**：
- ✅ **必须安装 `apache-flink` Python 包**：Flink 官方镜像只包含 Java 运行时，不包含 Python API
- ✅ **版本严格匹配**：PyFlink 2.1.1 兼容 Flink 2.0.x 运行时
- ✅ **AMD64 架构**：K8s 节点是 AMD64，本地 Mac（ARM64）需要跨平台构建

#### 4.2 构建步骤

```bash
cd /path/to/lemo_recommender

# 步骤1: 构建 flink-python 镜像（基础镜像）
docker buildx build --platform linux/amd64 \
  -t registry.cn-beijing.aliyuncs.com/lemo_zls/flink-python:latest \
  -f Dockerfile.flink-python \
  --push .

# 步骤2: 构建 flink-app 镜像（应用镜像）
docker buildx build --platform linux/amd64 \
  -t registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest \
  -f Dockerfile.flink-app \
  --push .
```

**说明**：
- `--platform linux/amd64`: 跨平台构建（Mac M1/M2 → AMD64）
- `--push`: 构建完成后自动推送到 ACR
- 必须先构建 `flink-python`，再构建 `flink-app`（依赖关系）

#### 4.3 验证镜像

```bash
# 验证镜像已推送
docker pull registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest

# 验证 PyFlink 是否安装（关键！）
docker run --rm registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest \
  python3 -c "import pyflink; print(f'PyFlink version: {pyflink.__version__}')"

# 预期输出：
# PyFlink version: 2.1.1

# 验证 Python 库
docker run --rm registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest \
  python3 -c "import pandas, numpy, kafka; print('✓ 依赖库正常')"
```

### 步骤5: 部署推荐服务

**使用现有的部署脚本：**

```bash
cd /path/to/lemo_recommender

# 部署 HTTP 和 gRPC 服务
bash k8s-deploy/deploy-http-grpc-service.sh

# 部署 Worker 服务
bash k8s-deploy/deploy-worker-service.sh

# 部署 Beat 服务
bash k8s-deploy/deploy-beat-service.sh

# 部署 Consumer 服务
bash k8s-deploy/deploy-consumer-service.sh
```

### 步骤6: 验证推荐服务部署

```bash
export KUBECONFIG=/root/k3s-jd-config.yaml

# 查看所有 Pod
kubectl get pods -n lemo-dev

# 查看 HTTP 服务日志，确认 Operator 模式已启用
kubectl logs -n lemo-dev deployment/lemo-service-recommender-http | grep -i operator
# 应该看到：
# ✓ Flink Operator 模式已启用（业界标准架构）
#   - Namespace: lemo-dev
#   - App Image: registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest
```

---

## 📋 Flink作业说明

### v2.0架构中的Flink作业

v2.0中，Flink作为**固定的实时特征服务**部署，包含4个核心作业：

#### 1. 用户实时特征计算（user_profile_updater.py）

**功能**：实时聚合用户行为，生成用户特征

**输入**：Kafka `user_behaviors` topic
```json
{
  "tenant_id": "demo",
  "scenario_id": "vlog_feed",
  "user_id": "user_001",
  "item_id": "video_123",
  "action_type": "VIEW",
  "timestamp": 1730800000000
}
```

**处理逻辑**：
- 1小时滚动窗口聚合
- 统计：观看次数、点赞次数、分享次数
- 计算活跃时段（早中晚）

**输出**：
- MongoDB `user_profiles` collection（持久化）
- Redis `user:profile:{user_id}` key（快速查询）

**用途**：Recall服务使用实时特征进行个性化召回

---

#### 2. 物品热度实时计算（item_hot_score_calculator.py）

**功能**：实时计算物品热度分数

**输入**：Kafka `user_behaviors` topic

**处理逻辑**：
- 1小时滑动窗口（每15分钟更新）
- 加权计算：`view×1 + like×2 + share×3`
- 考虑时间衰减（越新权重越高）

**输出**：
- Redis ZSET `hot:items:{tenant_id}:{scenario_id}`
- 只保留Top 1000物品
- 2小时过期

**用途**：HotItemsRecall使用热度分数进行热门召回

---

#### 3. 推荐指标实时统计（recommendation_metrics.py）

**功能**：实时计算推荐效果指标

**输入**：Kafka `user_behaviors` topic

**处理逻辑**：
- 1分钟滚动窗口聚合
- 统计：曝光数、点击数、CTR、平均观看时长、完播率

**输出**：
- Prometheus Pushgateway（监控指标）
- 供Grafana大盘展示

**指标示例**：
```
recommendation_ctr{tenant_id="demo",scenario_id="vlog_feed"} 0.035
recommendation_avg_watch_duration{tenant_id="demo",scenario_id="vlog_feed"} 45.2
```

**用途**：运营监控、AB实验效果评估

---

#### 4. 行为数据实时ETL（services/flink-realtime/main.py）

**功能**：Kafka → ClickHouse实时写入

**输入**：Kafka `user_behaviors` topic

**处理逻辑**：
- 数据清洗（去重、过滤无效数据）
- 格式转换（JSON → ClickHouse格式）
- 实时写入

**输出**：
- ClickHouse `user_behaviors` 表（OLAP）

**用途**：离线模型训练（DeepFM、Wide&Deep）使用ClickHouse数据

---

### 部署配置

**FlinkDeployment文件**：`k8s-deploy/flink-deployment-realtime-service.yaml`

```yaml
apiVersion: flink.apache.org/v1beta1
kind: FlinkDeployment
metadata:
  name: flink-realtime-features
  namespace: lemo-dev
spec:
  image: registry.cn-beijing.aliyuncs.com/lemo/recommender-flink:latest
  flinkVersion: v1_17
  flinkConfiguration:
    taskmanager.numberOfTaskSlots: "4"
    state.backend: rocksdb
    execution.checkpointing.interval: 60s
  jobManager:
    resource:
      memory: "1024m"
      cpu: 0.5
  taskManager:
    resource:
      memory: "1024m"
      cpu: 0.5
    replicas: 2
  job:
    jarURI: local:///opt/flink/usrlib/recommender.jar
    entryClass: "services.flink_realtime.main"
    parallelism: 4
    state: running
  envFrom:
  - configMapRef:
      name: lemo-services-config
```

**部署命令**：
```bash
kubectl apply -f k8s-deploy/flink-deployment-realtime-service.yaml
```

**查看状态**：
```bash
kubectl get flinkdeployment -n lemo-dev
kubectl logs -f -n lemo-dev -l app=flink-realtime-features,component=jobmanager
```

---

## 🚀 自动伸缩方案

### 伸缩模式对比

我们实现了**6种自动伸缩模式**，覆盖从固定资源到智能动态伸缩的所有场景：

| 模式 | 说明 | 适用场景 | 业界实践 |
|------|------|---------|---------|
| **disabled** | 禁用自动伸缩 | 流量稳定，资源固定 | - |
| **reactive** | Flink Reactive Mode | 根据可用资源自动调整并行度 | Flink 1.13+ |
| **hpa** | Kubernetes HPA | 根据 CPU/内存自动扩缩 TaskManager | AWS、阿里云 |
| **hpa_reactive** ⭐ | HPA + Reactive | 资源自动扩缩 + 并行度自动调整 | **字节跳动、美团** |
| **scheduled** | 定时伸缩 | 工作日高峰扩容，夜间缩容 | 美团、携程 |
| **scheduled_hpa** ⭐⭐ | 定时 + HPA | 定时设置基准 + HPA 动态调整 | **业界最佳实践** |

### 1. 资源档位（Resource Profiles）

预定义5个资源档位，每个档位包含推荐的副本范围：

| 档位 | CPU | 内存 | 副本范围 | QPS | 适用场景 |
|------|-----|------|---------|-----|---------|
| **micro** | 0.2核 | 256MB | 1-2 | < 100 | 测试/开发 |
| **small** | 0.5核 | 512MB | 1-3 | < 1K | 小规模生产 |
| **medium** | 1核 | 1GB | 2-5 | 1K-10K | 中等规模 |
| **large** | 2核 | 2GB | 2-10 | 10K-100K | 大规模 |
| **xlarge** | 4核 | 4GB | 3-20 | > 100K | 超大规模 |

### 2. Flink Reactive Mode

**特点**：根据可用 TaskManager 数量自动调整作业并行度

**配置示例**：
```json
{
  "resource_profile": "small",
  "autoscaler_mode": "reactive"
}
```

**生成的 Flink 配置**：
```yaml
flinkConfiguration:
  scheduler-mode: reactive
  jobmanager.adaptive-scheduler.min-parallelism-increase: "1"
  jobmanager.adaptive-scheduler.resource-stabilization-timeout: "10s"
```

**工作原理**：
1. TaskManager 数量增加 → 并行度自动增加
2. TaskManager 数量减少 → 并行度自动减少
3. 资源稳定期 10 秒，避免频繁调整

### 3. Kubernetes HPA

**特点**：根据 CPU/内存使用率自动扩缩 TaskManager 副本数

**配置示例**：
```json
{
  "resource_profile": "medium",
  "autoscaler_mode": "hpa",
  "target_cpu_utilization": 80,
  "min_replicas": 2,
  "max_replicas": 8
}
```

**生成的 HPA 配置**：
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 2
  maxReplicas: 8
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60   # 1 分钟稳定期
      policies:
        - type: Percent
          value: 100                    # 每次最多翻倍
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300  # 5 分钟稳定期
      policies:
        - type: Percent
          value: 50                     # 每次最多减半
          periodSeconds: 60
```

**工作原理**：
1. CPU 使用率 > 80% → 扩容（最快 1 分钟）
2. CPU 使用率 < 80% → 缩容（最快 5 分钟）
3. 扩容激进，缩容保守

### 4. HPA + Reactive（推荐）

**特点**：结合 HPA 和 Reactive Mode，实现双层自动伸缩

**配置示例**：
```json
{
  "resource_profile": "medium",
  "autoscaler_mode": "hpa_reactive"
}
```

**工作原理**：
```
流量增加
  ↓
CPU 使用率上升
  ↓
HPA 触发扩容（增加 TaskManager）
  ↓
Reactive Mode 检测到新的 TaskManager
  ↓
自动增加并行度
  ↓
处理能力提升
```

**优势**：
- ✅ 自动扩缩容（无需人工干预）
- ✅ 并行度自动调整（充分利用资源）
- ✅ 快速响应流量波动
- ✅ 业界最佳实践（字节跳动、美团在用）

### 5. 定时伸缩（Scheduled Scaling）

**特点**：按时间表自动调整资源，适合流量有规律的场景

#### 预定义策略

##### 5.1 工作日高峰策略（workday_peak）

**适用场景**：ToB 业务，工作日流量高，周末流量低

**配置示例**：
```json
{
  "resource_profile": "medium",
  "autoscaler_mode": "scheduled",
  "scaling_preset": "workday_peak"
}
```

**伸缩规则**：
| 时间 | Cron | 副本范围 | 说明 |
|------|------|---------|------|
| 周一-五 9:00 | `0 9 * * 1-5` | 3-10 | 早高峰扩容 |
| 周一-五 18:00 | `0 18 * * 1-5` | 1-3 | 晚高峰后缩容 |
| 周六 0:00 | `0 0 * * 6` | 1-2 | 周末缩容 |

**资源利用效果**：
```
周一      周二      周三      周四      周五      周六      周日
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│ 3-10   ││ 3-10   ││ 3-10   ││ 3-10   ││ 3-10   ││ 1-2    ││ 1-2    │ 副本数
│████████││████████││████████││████████││████████││██      ││██      │
│9:00-18:││9:00-18:││9:00-18:││9:00-18:││9:00-18:││全天    ││全天    │
│ 1-3    ││ 1-3    ││ 1-3    ││ 1-3    ││ 1-3    ││        ││        │
│██      ││██      ││██      ││██      ││██      ││        ││        │
│18:00+  ││18:00+  ││18:00+  ││18:00+  ││18:00+  ││        ││        │
└────────┘└────────┘└────────┘└────────┘└────────┘└────────┘└────────┘
```

##### 5.2 全天候高峰策略（24x7_peak）

**适用场景**：ToC 业务，全周都有流量，但白天高于夜间

**配置示例**：
```json
{
  "resource_profile": "medium",
  "autoscaler_mode": "scheduled",
  "scaling_preset": "24x7_peak"
}
```

**伸缩规则**：
| 时间 | Cron | 副本范围 | 说明 |
|------|------|---------|------|
| 每天 9:00 | `0 9 * * *` | 2-8 | 白天扩容 |
| 每天 23:00 | `0 23 * * *` | 1-3 | 夜间缩容 |

##### 5.3 自定义策略（custom）

**配置示例**：
```json
{
  "resource_profile": "medium",
  "autoscaler_mode": "scheduled",
  "scaling_schedules": [
    {
      "name": "morning-scale-up",
      "cron": "0 8 * * 1-5",
      "min_replicas": 5,
      "max_replicas": 15
    },
    {
      "name": "noon-scale-down",
      "cron": "0 12 * * 1-5",
      "min_replicas": 2,
      "max_replicas": 8
    },
    {
      "name": "evening-scale-up",
      "cron": "0 19 * * 1-5",
      "min_replicas": 4,
      "max_replicas": 12
    }
  ]
}
```

#### 实现机制

定时伸缩通过 **Kubernetes CronJob** 实现：

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: job-example-scale-morning-scale-up
spec:
  schedule: "0 9 * * 1-5"
  concurrencyPolicy: Forbid  # 禁止并发执行
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: lemo-service-recommender-sa
          containers:
            - name: kubectl
              image: bitnami/kubectl:latest
              command:
                - sh
                - -c
                - |
                  echo "定时伸缩: morning-scale-up"
                  # 如果有 HPA，更新 HPA
                  if kubectl get hpa job-example-hpa -n lemo-dev; then
                    kubectl patch hpa job-example-hpa -n lemo-dev \
                      --type merge -p '{"spec":{"minReplicas":3,"maxReplicas":10}}'
                  else
                    # 否则直接更新 FlinkDeployment
                    kubectl patch flinkdeployment job-example -n lemo-dev \
                      --type merge -p '{"spec":{"taskManager":{"replicas":3}}}'
                  fi
```

**查看定时任务**：
```bash
# 查看所有 CronJob
kubectl get cronjob -n lemo-dev

# 查看 CronJob 详情
kubectl describe cronjob job-example-scale-morning-scale-up -n lemo-dev

# 查看 CronJob 执行历史
kubectl get jobs -n lemo-dev -l app=flink-job-scaler

# 手动触发一次（测试）
kubectl create job --from=cronjob/job-example-scale-morning-scale-up \
  manual-test -n lemo-dev
```

### 6. 定时伸缩 + HPA（业界最佳）

**特点**：定时设置基准副本范围，HPA 在此基础上动态调整

**配置示例**：
```json
{
  "resource_profile": "medium",
  "autoscaler_mode": "scheduled_hpa",
  "scaling_preset": "workday_peak",
  "target_cpu_utilization": 75
}
```

**工作原理**：
```
周一 9:00 (CronJob 触发)
  ↓
设置 HPA: minReplicas=3, maxReplicas=10
  ↓
流量增加，CPU 使用率 > 75%
  ↓
HPA 自动扩容（3 → 5 → 7 → 10）
  ↓
流量减少，CPU 使用率 < 75%
  ↓
HPA 自动缩容（10 → 7 → 5 → 3）
  ↓
周一 18:00 (CronJob 触发)
  ↓
设置 HPA: minReplicas=1, maxReplicas=3
  ↓
HPA 自动将副本数缩减到 1-3 范围
```

**优势**：
- ✅ **定时设置基准**：根据业务规律预设资源范围
- ✅ **HPA 动态调整**：在基准范围内根据负载自动伸缩
- ✅ **成本最优**：夜间/周末自动降低资源下限
- ✅ **性能保障**：高峰期自动提高资源上限

**成本对比**：
| 方案 | 平均副本数 | 月成本 | 备注 |
|------|-----------|--------|------|
| 固定 10 副本 | 10 | ¥10,000 | 资源浪费 |
| 纯 HPA (1-10) | 6 | ¥6,000 | 夜间仍保持高位 |
| scheduled_hpa | 3.5 | ¥3,500 | **节省 65%** |

### 7. 业界实践对比

| 公司 | 方案 | 配置 | 效果 |
|------|------|------|------|
| **字节跳动** | hpa_reactive | min:2, max:20, CPU:80% | 流量波动 10x，自动应对 |
| **美团** | scheduled_hpa | 工作日 9-18 扩容 | 成本降低 60% |
| **阿里云** | 资源档位 + HPA | small/medium/large | 用户选档位，系统自动伸缩 |
| **AWS Kinesis** | KPU 自动伸缩 | 1-32 KPU | 按实际使用付费 |
| **我们的实现** | 🎯 **6 种模式全覆盖** | 资源档位 + HPA + Reactive + 定时 | **业界最全方案** |

### 8. 配置参考

#### 场景1：测试环境
```json
{
  "resource_profile": "micro",
  "autoscaler_mode": "disabled"
}
```
- 0.2核/256MB，固定 1 副本
- 成本最低，适合功能测试

#### 场景2：小规模生产（流量稳定）
```json
{
  "resource_profile": "small",
  "autoscaler_mode": "hpa",
  "min_replicas": 1,
  "max_replicas": 3,
  "target_cpu_utilization": 80
}
```
- 0.5核/512MB，1-3 副本自动调整
- 简单有效，适合流量稳定的小应用

#### 场景3：中等规模生产（流量波动）
```json
{
  "resource_profile": "medium",
  "autoscaler_mode": "hpa_reactive"
}
```
- 1核/1GB，2-5 副本自动调整
- HPA + Reactive，双层自动伸缩
- 适合流量有波动的中型应用

#### 场景4：ToB 业务（工作日高峰）
```json
{
  "resource_profile": "medium",
  "autoscaler_mode": "scheduled_hpa",
  "scaling_preset": "workday_peak",
  "target_cpu_utilization": 75
}
```
- 工作日 9-18 扩容，夜间/周末缩容
- HPA 在基准范围内动态调整
- **成本节省 60%+**

#### 场景5：大规模生产（高并发）
```json
{
  "resource_profile": "large",
  "autoscaler_mode": "hpa_reactive",
  "min_replicas": 5,
  "max_replicas": 20,
  "target_cpu_utilization": 70
}
```
- 2核/2GB，5-20 副本
- 更低的 CPU 目标（70%），更快扩容
- 适合高并发、对延迟敏感的应用

---

## 🔍 运维管理

### 查看作业状态

```bash
export KUBECONFIG=/root/k3s-jd-config.yaml

# 查看所有 FlinkDeployment
kubectl get flinkdeployment -n lemo-dev

# 输出示例：
# NAME                STATUS    JOB-STATUS   AGE
# job-example-py      READY     RUNNING      5m
# job-example-jar     READY     FINISHED     10m

# 查看详细信息
kubectl describe flinkdeployment job-example-py -n lemo-dev

# 查看作业 Pod
kubectl get pods -n lemo-dev -l app=job-example-py
```

### 查看作业日志

```bash
# JobManager 日志
kubectl logs -n lemo-dev -l app=job-example-py,component=jobmanager

# TaskManager 日志
kubectl logs -n lemo-dev -l app=job-example-py,component=taskmanager

# 实时跟踪
kubectl logs -f -n lemo-dev -l app=job-example-py,component=jobmanager
```

### 停止作业

**方式1: 通过前端/API**
```bash
POST /api/v1/flink/jobs/{job_id}/stop
```

**方式2: 直接删除 CRD**
```bash
kubectl delete flinkdeployment job-example-py -n lemo-dev
```

### 暂停/恢复作业（Savepoint）

```bash
# 暂停作业（创建 Savepoint）
kubectl patch flinkdeployment job-example-py -n lemo-dev \
  --type merge -p '{"spec":{"job":{"state":"suspended"}}}'

# 恢复作业（从 Savepoint）
kubectl patch flinkdeployment job-example-py -n lemo-dev \
  --type merge -p '{"spec":{"job":{"state":"running"}}}'
```

### 扩缩容

#### 手动扩缩容

```bash
# 调整 TaskManager 副本数
kubectl patch flinkdeployment job-example-py -n lemo-dev \
  --type merge -p '{"spec":{"taskManager":{"replicas":3}}}'
```

#### 查看自动伸缩状态

```bash
# 查看 HPA 状态
kubectl get hpa -n lemo-dev
kubectl describe hpa job-example-py-hpa -n lemo-dev

# 查看定时伸缩 CronJob
kubectl get cronjob -n lemo-dev
kubectl get cronjob -n lemo-dev -l deployment=job-example-py

# 查看 CronJob 执行历史
kubectl get jobs -n lemo-dev -l app=flink-job-scaler

# 查看最近一次 CronJob 执行日志
kubectl logs -n lemo-dev -l app=flink-job-scaler --tail=50
```

#### 调整 HPA 配置

```bash
# 调整 CPU 目标使用率
kubectl patch hpa job-example-py-hpa -n lemo-dev \
  --type merge -p '{"spec":{"metrics":[{"type":"Resource","resource":{"name":"cpu","target":{"type":"Utilization","averageUtilization":70}}}]}}'

# 调整副本范围
kubectl patch hpa job-example-py-hpa -n lemo-dev \
  --type merge -p '{"spec":{"minReplicas":2,"maxReplicas":8}}'
```

#### 手动触发定时伸缩

```bash
# 测试定时伸缩任务（不等待 Cron 时间）
kubectl create job --from=cronjob/job-example-py-scale-morning-scale-up \
  manual-test-$(date +%s) -n lemo-dev

# 查看执行结果
kubectl logs -n lemo-dev job/manual-test-1234567890
```

---

## 🛠️ 故障排查

### 问题1: Operator Pod 无法启动

**症状：**
```bash
kubectl get pods -n flink-operator-system
# NAME                                     READY   STATUS             RESTARTS   AGE
# flink-kubernetes-operator-xxx            0/1     ImagePullBackOff   0          5m
```

**排查：**
```bash
# 查看 Pod 详情
kubectl describe pod -n flink-operator-system flink-kubernetes-operator-xxx

# 查看日志
kubectl logs -n flink-operator-system flink-kubernetes-operator-xxx
```

**解决：**
- 检查镜像地址是否正确
- 检查镜像仓库是否可访问
- 确认 K8s 集群可以访问 GitHub Container Registry

### 问题2: FlinkDeployment 创建失败

**症状：**
```bash
kubectl get flinkdeployment -n lemo-dev
# NAME             STATUS   ERROR
# job-example-py   FAILED   Job submission failed
```

**排查：**
```bash
# 查看 CRD 详情
kubectl describe flinkdeployment job-example-py -n lemo-dev

# 查看 Operator 日志
kubectl logs -n flink-operator-system -l app.kubernetes.io/name=flink-kubernetes-operator
```

**常见原因：**
1. 镜像拉取失败 → 检查镜像地址和拉取凭证
2. 资源不足 → 检查 K8s 节点资源
3. RBAC 权限不足 → 检查 ServiceAccount 权限
4. 配置错误 → 检查 CRD YAML 语法

### 问题3: 作业启动后立即失败

**症状：**
```bash
kubectl get pods -n lemo-dev -l app=job-example-py
# NAME                     READY   STATUS       RESTARTS   AGE
# job-example-py-jm-xxx    0/1     Error        0          1m
```

**排查：**
```bash
# 查看 JobManager 日志
kubectl logs -n lemo-dev job-example-py-jm-xxx

# 常见错误：
# 1. Python 脚本下载失败
# 2. JAR 依赖找不到
# 3. Kafka/MongoDB/Redis 连接失败
# 4. Python 代码语法错误
```

**解决：**
```bash
# 1. 检查脚本 URL 是否可访问
curl -I https://file.lemo-ai.com/example.py

# 2. 检查 JAR 文件是否存在
kubectl exec -it job-example-py-tm-xxx -n lemo-dev -- \
  ls -l /opt/flink/opt/

# 3. 检查网络连接
kubectl exec -it job-example-py-tm-xxx -n lemo-dev -- \
  curl -v 111.228.39.41:9092
```

### 问题4: gRPC 服务报 ModuleNotFoundError

**症状：**
```
ModuleNotFoundError: No module named 'app.utils.logger'
```

**解决：**
- 确保 `operator_job_manager.py` 使用 `from loguru import logger`
- 重新构建并部署服务

### 问题5: HPA 不生效

**症状：**
```bash
kubectl get hpa -n lemo-dev
# NAME                 REFERENCE                    TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# job-example-py-hpa   FlinkDeployment/job-example  <unknown>/80%   2   8    0          5m
```

**排查：**
```bash
# 1. 检查 metrics-server 是否安装
kubectl get deployment metrics-server -n kube-system

# 2. 如果没有，安装 metrics-server
kubectl apply -f https://ghproxy.com/https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 3. 检查 Pod 是否有资源请求（HPA 需要 resources.requests）
kubectl get flinkdeployment job-example-py -n lemo-dev -o yaml | grep -A 5 resources
```

**解决：**
- 确保 K8s 集群已安装 `metrics-server`
- 确保 FlinkDeployment 的 `jobManager` 和 `taskManager` 都配置了 `cpu` 和 `memory`

### 问题6: 定时伸缩 CronJob 不执行

**症状：**
```bash
kubectl get cronjob -n lemo-dev
# NAME                                   SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE
# job-example-py-scale-morning-scale-up  0 9 * * 1-5   False     0        <none>          1h
```

**排查：**
```bash
# 1. 检查 CronJob 详情
kubectl describe cronjob job-example-py-scale-morning-scale-up -n lemo-dev

# 2. 检查时区（K8s CronJob 使用 UTC 时间）
date -u

# 3. 手动触发一次测试
kubectl create job --from=cronjob/job-example-py-scale-morning-scale-up \
  manual-test -n lemo-dev

# 4. 查看执行日志
kubectl logs -n lemo-dev job/manual-test
```

**常见原因：**
1. **时区问题**：CronJob 使用 UTC 时间，需要转换本地时间
   - 例如：北京时间 9:00 = UTC 1:00，Cron 应为 `0 1 * * 1-5`
2. **RBAC 权限不足**：ServiceAccount 没有 patch HPA/FlinkDeployment 的权限
3. **CronJob 被暂停**：`suspend: true`

**解决：**
```bash
# 调整 Cron 表达式（考虑时区）
kubectl patch cronjob job-example-py-scale-morning-scale-up -n lemo-dev \
  --type merge -p '{"spec":{"schedule":"0 1 * * 1-5"}}'

# 取消暂停
kubectl patch cronjob job-example-py-scale-morning-scale-up -n lemo-dev \
  --type merge -p '{"spec":{"suspend":false}}'
```

### 问题7: Pod Pending（资源不足）

**症状：**
```bash
kubectl get pods -n lemo-dev
# NAME                     READY   STATUS    RESTARTS   AGE
# job-example-py-tm-xxx    0/1     Pending   0          5m
```

**排查：**
```bash
# 查看 Pod 事件
kubectl describe pod job-example-py-tm-xxx -n lemo-dev

# 常见错误：
# Events:
#   Type     Reason            Message
#   ----     ------            -------
#   Warning  FailedScheduling  0/1 nodes are available: 1 Insufficient cpu
```

**解决：**
1. **降低资源档位**：从 `medium` 改为 `small` 或 `micro`
2. **增加节点资源**：扩容 K8s 集群
3. **调整 HPA 副本上限**：避免超过节点资源上限

```json
{
  "resource_profile": "micro",
  "autoscaler_mode": "hpa",
  "max_replicas": 2
}
```

---

## 🔧 高级功能：动态作业提交

> **说明**：此功能用于后台管理，允许管理员临时提交定制化Flink作业（数据回填、临时分析等）

### 使用场景

| 场景 | 说明 | 示例 |
|------|------|------|
| **数据回填** | 补充历史数据 | 重新计算过去30天的用户特征 |
| **临时分析** | 特殊场景统计 | 分析某个营销活动的转化率 |
| **实验性作业** | 测试新算法 | 测试新的热度计算公式 |
| **一次性任务** | 数据迁移 | 从旧系统迁移用户画像数据 |

### 后台管理流程

#### 1. 创建作业模板（后台界面）

```json
{
  "template_id": "data_backfill_20241105",
  "name": "用户特征数据回填",
  "description": "补充10月份的用户特征数据",
  "job_type": "PYTHON_SCRIPT",
  "config": {
    "script_path": "https://file.lemo-ai.com/backfill_user_features.py",
    "parallelism": 4,
    "jar_files": [
      "/opt/flink/opt/flink-sql-connector-kafka-3.0.2-1.18.jar"
    ],
    "args": {
      "start_date": "2024-10-01",
      "end_date": "2024-10-31"
    }
  }
}
```

#### 2. 提交作业请求（API调用）

```bash
POST /api/v1/flink/jobs/submit
Content-Type: application/json

{
  "template_id": "data_backfill_20241105",
  "job_config": {
    "parallelism": 8,
    "resource_profile": "large"
  }
}
```

#### 3. 后端处理流程

```python
# app/services/flink/job_manager.py
async def submit_job(self, template, request):
    # 1. 生成FlinkDeployment YAML
    crd_yaml = self.crd_generator.generate_yaml(template, request)
    
    # 2. 创建K8s CRD
    self.k8s_client.create_namespaced_custom_object(
        group="flink.apache.org",
        version="v1beta1",
        namespace="lemo-dev",
        plural="flinkdeployments",
        body=crd_yaml
    )
    
    # 3. 返回作业ID
    return {
        "job_id": "job-backfill-20241105-abc123",
        "status": "RUNNING"
    }
```

#### 4. 查询作业状态

```bash
GET /api/v1/flink/jobs/job-backfill-20241105-abc123

# 响应
{
  "job_id": "job-backfill-20241105-abc123",
  "status": "RUNNING",
  "flink_job_id": "a1b2c3d4e5f6",
  "start_time": "2024-11-05T10:00:00Z",
  "progress": 45.2,
  "metrics": {
    "records_processed": 12000000,
    "records_per_second": 50000
  }
}
```

#### 5. 停止作业

```bash
DELETE /api/v1/flink/jobs/job-backfill-20241105-abc123
```

### 支持的作业类型

| 类型 | 说明 | 配置示例 |
|------|------|---------|
| **PYTHON_SCRIPT** | Python脚本作业 | `{"script_path": "https://..."}` |
| **JAR** | Java JAR作业 | `{"jar_path": "https://...", "main_class": "..."}` |
| **SQL** | Flink SQL作业 | `{"sql": "CREATE TABLE ..."}` |

### 与固定服务的对比

| 对比项 | 固定实时服务（v2.0主流） | 动态作业提交（高级功能） |
|--------|------------------------|------------------------|
| **用途** | 7×24实时特征计算 | 临时/一次性任务 |
| **部署** | kubectl apply静态部署 | API动态创建 |
| **数量** | 1个FlinkDeployment | N个FlinkDeployment |
| **管理** | Flink Operator自动 | 后台手动管理 |
| **资源** | 固定资源 | 按需分配 |
| **适用场景** | 生产环境核心服务 | 数据回填、临时分析 |

### 实现代码位置

| 组件 | 文件路径 | 说明 |
|------|---------|------|
| **API接口** | `app/api/v1/flink_jobs.py` | HTTP API定义 |
| **作业管理器** | `app/services/flink/job_manager.py` | 作业提交/查询/停止 |
| **Operator管理器** | `app/services/flink/operator_job_manager.py` | K8s Operator集成 |
| **CRD生成器** | `app/services/flink/crd_generator.py` | FlinkDeployment YAML生成 |

---

##  📚 参考资料

- **Flink Kubernetes Operator 官方文档**: https://nightlies.apache.org/flink/flink-kubernetes-operator-docs-main/
- **Flink 官方文档**: https://nightlies.apache.org/flink/flink-docs-release-1.19/
- **Kubernetes CRD 文档**: https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/
- **项目 GitHub**: https://github.com/AndrewLiuZhangZong/lemo_recommender

---

## 📝 快速参考

### 常用命令

```bash
# 设置 kubeconfig
export KUBECONFIG=/root/k3s-jd-config.yaml

# 查看 Operator
kubectl get pods -n flink-operator-system

# 查看固定实时服务
kubectl get flinkdeployment flink-realtime-features -n lemo-dev
kubectl logs -f -n lemo-dev -l app=flink-realtime-features,component=jobmanager

# 查看所有动态作业
kubectl get flinkdeployment -n lemo-dev | grep -v flink-realtime-features

# 查看作业详情
kubectl describe flinkdeployment <job-name> -n lemo-dev

# 删除动态作业
kubectl delete flinkdeployment <job-name> -n lemo-dev

# 重启推荐服务
kubectl rollout restart deployment/lemo-service-recommender-http -n lemo-dev
```

### 配置文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| **固定实时服务** | `k8s-deploy/flink-deployment-realtime-service.yaml` | v2.0核心部署文件 |
| Operator 安装脚本 | `scripts/install_flink_operator.sh` | 安装 Flink Operator |
| Flink作业代码 | `flink_jobs/*.py` | 4个核心Flink作业 |
| Job Manager | `app/services/flink/job_manager.py` | 动态作业管理 |
| Operator Manager | `app/services/flink/operator_job_manager.py` | Operator 集成 |
| CRD Generator | `app/services/flink/crd_generator.py` | CRD YAML 生成 |

---

**文档版本**: v2.0  
**更新时间**: 2024-11-05  
**维护者**: Lemo 推荐系统团队


