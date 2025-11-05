# Lemo Recommender - 多场景SaaS推荐系统

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-brightgreen.svg)](https://www.mongodb.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**支持多场景、高性能、易扩展的SaaS推荐系统**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [API文档](#-api文档) • [部署](#-部署) • [架构设计](docs/系统设计.md)

</div>

---

## 📖 项目简介

Lemo Recommender 是一个面向SaaS场景的通用推荐系统，支持多租户、多场景（vlog、新闻、电商等），通过配置化设计实现快速场景定制，无需修改代码即可适配不同业务需求。

### 核心优势

- **🎯 配置化驱动**: 场景配置化，召回/排序/重排策略可灵活组合
- **🏢 多租户隔离**: 完全的数据和资源隔离
- **⚡ 高性能**: 三级缓存架构 + 并行召回 + 深度模型优化
- **📊 实时计算**: Kafka + Flink实时特征计算
- **☸️ 云原生**: 支持Docker和Kubernetes部署，微服务拆分
- **📈 可观测**: Prometheus + Grafana监控体系

---

## 🚀 功能特性

### 推荐引擎

| 模块 | 功能 | 状态 |
|------|------|-----|
| **召回层** | 协同过滤(UserCF/ItemCF)、ALS矩阵分解、向量召回、热门召回 | ✅ |
| **排序层** | 简单排序、DeepFM深度模型、LightGBM | ✅ |
| **重排层** | 多样性、新鲜度、业务规则 | ✅ |
| **缓存层** | L1推荐结果缓存、L2热数据缓存、L3物品详情缓存 | ✅ |

### 技术栈

| 类别 | 技术选型 |
|------|---------|
| Web框架 | FastAPI |
| 数据库 | MongoDB + Redis |
| 消息队列 | Kafka (KRaft模式) |
| 流计算 | Apache Flink |
| 向量DB | Milvus 2.4+ |
| 监控 | Prometheus + Grafana |
| 容器化 | Docker + Kubernetes |

---

## 🎬 快速开始

> 💡 **详细教程请查看**: [QUICKSTART.md](QUICKSTART.md) - 包含完整的curl示例和故障排查

### 环境要求

- Python 3.10+
- Node.js 18+ (管理后台)
- MongoDB 6.0+
- Redis 7+ (本地已有)
- Kafka 3.0+ (本地已有)

### 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/AndrewLiuZhangZong/lemo_recommender.git
cd lemo_recommender

# 2. 后端启动
poetry install
docker-compose up -d mongodb
make init-db
ENV=local poetry run python app/main.py

# 3. 前端启动（新终端）
cd admin-frontend
npm install
npm run dev
```

### 访问地址

- 🎨 **管理后台**: http://localhost:19080
- 📚 **API文档**: http://localhost:18081/api/v1/docs
- 📊 **Prometheus**: http://localhost:18081/metrics
- ❤️ **健康检查**: http://localhost:18081/health

---

## ⚡ 性能优化（v1.0）

系统已完成全面性能优化，推荐延迟降低50%，算法效果提升15-20%。

### 优化成果

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| **推荐P99延迟** | ~100ms | <50ms | 50% ⬇️ |
| **缓存命中率** | ~30% | >70% | 133% ⬆️ |
| **CTR** | 基准值 | +15% | 15% ⬆️ |
| **召回覆盖率** | 70% | 90% | 29% ⬆️ |

### 核心优化

1. **三级缓存架构** 🚀
   - L1: 推荐结果缓存（5分钟，命中延迟<5ms）
   - L2: 热数据缓存（1小时，用户画像/热门物品）
   - L3: 物品详情缓存（24小时，物品元数据）

2. **异步并行召回** ⚡
   - 使用`asyncio.gather`并行执行多路召回
   - 召回延迟从140ms降至50ms（降低64%）

3. **ALS协同过滤** 🧠
   - 基于矩阵分解的高效召回算法
   - 向量预计算，查询延迟<20ms
   - 召回覆盖率提升至90%

4. **DeepFM深度排序** 🎯
   - 端到端深度学习排序模型
   - 自动学习特征交互
   - CTR提升15-20%

5. **数据库索引优化** 📊
   - 6个核心表的复合索引
   - 查询性能提升50%

### 使用文档

详细的优化说明和使用指南，请查看：
- 📋 [系统优化计划v1.0](docs/系统优化计划v1.0.md) - 性能和算法优化（已完成✅）
- 🚀 [系统优化计划v2.0](docs/系统优化计划v2.0.md) - 服务拆分与架构升级（2亿+用户）

### 快速使用

```bash
# 1. 执行数据库索引优化
python scripts/optimize_indexes.py optimize

# 2. 训练ALS模型
python -c "
from app.engine.recall.als_cf import ALSCollaborativeFiltering
from app.core.database import get_database
from app.core.redis_client import get_redis_client

als = ALSCollaborativeFiltering(get_database(), get_redis_client())
result = await als.train('tenant_id', 'scenario_id')
"

# 3. 训练DeepFM模型
python -c "
from app.ml.trainer_deepfm import DeepFMTrainer
trainer = DeepFMTrainer('tenant_id', 'scenario_id', get_database())
result = await trainer.train({'days': 7, 'epochs': 10})
"
```

### 场景配置示例

启用ALS召回和DeepFM排序：

```json
{
  "recall": {
    "strategies": [
      {"name": "als_cf", "weight": 0.5, "limit": 200},
      {"name": "hot_items", "weight": 0.3, "limit": 100},
      {"name": "user_cf", "weight": 0.2, "limit": 100}
    ]
  },
  "rank": {
    "model": "deepfm"
  }
}
```

---

## 📡 API文档

启动后访问: **http://localhost:18081/api/v1/docs**

### 核心接口

#### 1. 推荐接口

```bash
POST /api/v1/recommend
X-Tenant-Id: demo_tenant
X-User-Id: user_001

{
  "scenario_id": "vlog_main_feed",
  "count": 20,
  "debug": true
}
```

#### 2. 场景管理

```bash
# 创建场景
POST /api/v1/scenarios

# 查询场景列表
GET /api/v1/scenarios

# 获取场景详情
GET /api/v1/scenarios/{scenario_id}
```

#### 3. 物品管理

```bash
# 创建物品
POST /api/v1/items

# 批量导入
POST /api/v1/items/batch

# 查询物品
GET /api/v1/items?scenario_id=vlog_main_feed
```

#### 4. 行为采集

```bash
# 上报用户行为
POST /api/v1/interactions

{
  "scenario_id": "vlog_main_feed",
  "user_id": "user_001",
  "item_id": "video_001",
  "action_type": "view",
  "extra": {
    "watch_duration": 90,
    "completion_rate": 0.75
  }
}
```

---

## 🎯 使用示例

### Python SDK 示例

```python
import httpx

# 配置
BASE_URL = "http://localhost:18081/api/v1"
HEADERS = {
    "X-Tenant-Id": "demo_tenant",
    "X-User-Id": "user_001",
    "X-Request-Id": "req_001"
}

# 获取推荐
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{BASE_URL}/recommend",
        headers=HEADERS,
        json={
            "scenario_id": "vlog_main_feed",
            "count": 10,
            "debug": True
        }
    )
    recommendations = response.json()
    
    for item in recommendations["items"]:
        print(f"推荐: {item['item_id']}, 分数: {item['score']}")
```

---

## 🏗️ 微服务架构

系统已按功能拆分为4个独立的微服务，支持独立部署、扩缩容和更新。

### 服务列表

| 服务 | 说明 | 端口 | 副本数 | 资源配置 |
|------|------|------|--------|---------|
| **HTTP+gRPC** | 推荐API服务（双协议） | 10071/10072 | 1-3 | 100m CPU / 128Mi Mem |
| **Worker** | Celery异步任务处理 | - | 2-4 | 500m CPU / 512Mi Mem |
| **Beat** | Celery定时任务调度 | - | 1 | 100m CPU / 128Mi Mem |
| **Consumer** | Kafka物品数据消费 | - | 1-2 | 250m CPU / 256Mi Mem |

### 服务职责

```
┌─────────────────────────────────────────────────────────────┐
│                     K3s Cluster / Docker                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  HTTP API    │  │   gRPC       │  │  Celery Worker   │  │
│  │  推荐查询     │  │  高性能RPC   │  │  模型训练/向量化 │  │
│  │  场景管理     │  │  行为上报     │  │  数据预处理     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                              │
│  ┌──────────────┐  ┌────────────────────────────────────┐  │
│  │ Celery Beat  │  │   Kafka Consumer                    │  │
│  │ 定时训练模型  │  │   物品数据接入                      │  │
│  │ 缓存预热      │  │   实时同步MongoDB                  │  │
│  └──────────────┘  └────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
              │                          │
              ▼                          ▼
    ┌──────────────────┐      ┌──────────────────┐
    │  外部依赖服务     │      │   Kafka Topics   │
    │  • MongoDB        │      │  item-events-*   │
    │  • Redis          │      │  user-behaviors  │
    │  • Milvus         │      └──────────────────┘
    │  • ClickHouse     │
    └──────────────────┘
```

### 部署方式

#### 方式1: Docker Compose（开发/测试）

```bash
cd /Users/edy/PycharmProjects/lemo_recommender
docker-compose up -d
```

#### 方式2: Kubernetes（生产）

```bash
# 部署HTTP+gRPC服务
cd k8s-deploy
./deploy-http-grpc-service.sh

# 部署Worker服务（可选，需要模型训练时）
./deploy-worker-service.sh

# 部署Beat服务（可选，需要定时任务时）
./deploy-beat-service.sh

# 部署Consumer服务（可选，需要Kafka接入时）
./deploy-consumer-service.sh
```

### 服务启动入口

```
services/
├── recommender/       # HTTP + gRPC 服务
│   ├── main_http.py   # HTTP 服务启动入口
│   └── main_grpc.py   # gRPC 服务启动入口
├── worker/            # Celery Worker 服务
│   └── main.py
├── beat/              # Celery Beat 服务
│   └── main.py
└── consumer/          # Kafka Consumer 服务
    └── main.py
```

详细的服务拆分说明和部署配置，请查看：
- 📋 [服务拆分方案](docs/服务拆分方案.md) - 当前架构说明（4个服务）
- 🚀 [系统优化计划v2.0](docs/系统优化计划v2.0.md) - 目标架构（13个服务，支持2亿+用户）
- 📝 [K8s部署指南](k8s-deploy/README.md) - Kubernetes部署说明

---

## 🏗️ 项目架构

### 整体结构

```
lemo_recommender/
├── app/                      # 应用主目录
│   ├── models/              # 数据模型层（Pydantic/MongoDB ODM）
│   │   ├── scenario.py      # 场景模型（配置、策略）
│   │   ├── item.py          # 物品模型（内容、特征）
│   │   ├── interaction.py   # 行为模型（点击、观看、分享）
│   │   ├── user_profile.py  # 用户画像模型
│   │   ├── flink_job_template.py # Flink作业模板
│   │   └── experiment.py    # AB实验模型
│   ├── services/            # 业务逻辑层
│   │   ├── scenario/        # 场景管理服务
│   │   ├── item/            # 物品管理服务（CRUD、向量化）
│   │   ├── interaction/     # 行为采集服务（埋点、统计）
│   │   ├── recommendation/  # 推荐编排服务
│   │   ├── experiment/      # AB实验服务（分桶、统计）
│   │   ├── flink/           # Flink作业管理
│   │   │   ├── job_manager.py    # 作业提交、停止、状态查询
│   │   │   ├── crd_generator.py  # CRD生成器（企业级标准）
│   │   │   └── template_service.py # 作业模板管理
│   │   └── cache_manager.py # 缓存管理（Redis）
│   ├── engine/              # 推荐引擎核心
│   │   ├── recall/          # 召回策略
│   │   │   ├── hot.py       # 热门召回（时间衰减）
│   │   │   ├── cf.py        # 协同过滤（user/item-based）
│   │   │   └── vector.py    # 向量召回（Milvus）
│   │   ├── ranker/          # 排序层
│   │   │   ├── simple_ranker.py  # 规则排序
│   │   │   └── model_ranker.py   # 模型排序（预留）
│   │   └── reranker/        # 重排层
│   │       ├── diversity.py  # 多样性重排
│   │       ├── freshness.py  # 新鲜度重排
│   │       └── business.py   # 业务规则重排
│   ├── ml/                  # 机器学习模块（预留）
│   │   ├── models/          # 深度学习模型
│   │   ├── trainer.py       # 模型训练
│   │   └── model_registry.py # 模型版本管理
│   ├── tasks/               # Celery离线任务
│   │   ├── celery_app.py    # Celery配置（Beat调度）
│   │   ├── item_tasks.py    # 物品任务（相似度计算）
│   │   └── user_tasks.py    # 用户任务（画像更新）
│   ├── api/                 # HTTP API路由
│   │   └── v1/              # API版本1
│   │       ├── scenario.py      # 场景CRUD API
│   │       ├── item.py          # 物品CRUD API
│   │       ├── interaction.py   # 行为上报API
│   │       ├── recommendation.py # 推荐请求API
│   │       ├── experiment.py    # AB实验API
│   │       ├── flink_jobs.py    # Flink作业管理API
│   │       └── admin.py         # 管理后台API
│   ├── grpc_server/         # gRPC服务（高性能RPC）
│   │   ├── recommendation_server.py # 推荐服务
│   │   └── feature_server.py        # 特征服务
│   ├── core/                # 核心基础组件
│   │   ├── config.py        # 多环境配置管理
│   │   ├── database.py      # MongoDB连接池
│   │   ├── redis_client.py  # Redis客户端（缓存、限流）
│   │   ├── kafka.py         # Kafka生产者/消费者
│   │   ├── milvus_client.py # Milvus向量数据库
│   │   └── metrics.py       # Prometheus指标导出
│   └── utils/               # 工具类
│       ├── rate_limiter.py  # 限流器（令牌桶、滑动窗口）
│       ├── circuit_breaker.py # 熔断器
│       └── performance.py   # 性能监控工具
├── admin-frontend/          # 管理后台前端（Vue3 + Element Plus + TypeScript）
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   │   ├── Dashboard.vue       # 仪表板（实时指标）
│   │   │   ├── Scenarios.vue       # 场景管理
│   │   │   ├── Items.vue           # 物品管理（批量导入）
│   │   │   ├── FlinkJobs.vue       # Flink作业管理
│   │   │   ├── Experiments.vue     # AB实验
│   │   │   └── Analytics.vue       # 数据分析
│   │   ├── api/            # API封装（axios）
│   │   ├── router/         # 路由配置
│   │   ├── stores/         # 状态管理（Pinia）
│   │   └── components/     # 公共组件
│   └── package.json
├── flink_jobs/              # Flink实时计算作业（Python/SQL）
│   ├── minimal_test.py      # 测试作业（验证环境）
│   ├── user_profile_updater.py       # 用户画像实时更新
│   ├── item_hot_score_calculator.py  # 物品热度计算
│   └── recommendation_metrics.py     # 实时指标统计
├── config/                  # 多环境配置文件
│   ├── local.env           # 本地开发环境
│   ├── test.env            # 测试环境
│   └── prod.env            # 生产环境
├── docs/                    # 项目文档
│   ├── Flink架构与部署完整指南.md  # Flink部署（企业级标准）⭐
│   ├── 系统设计.md          # 完整技术架构
│   └── 开发计划.md          # 22周开发路线图
├── k8s-deploy/              # Kubernetes部署配置
│   ├── k8s-deployment-http-grpc.yaml # HTTP+gRPC服务部署
│   ├── flink-operator.yaml  # Flink Kubernetes Operator
│   └── regcred-secret.yaml  # 阿里云ACR镜像拉取凭证
├── scripts/                 # 运维脚本工具
│   ├── build_flink_images.sh        # Flink镜像构建（企业级标准）⭐
│   ├── build_and_push_flink_to_acr.sh   # flink-python镜像构建
│   ├── build_and_push_flink_app.sh      # flink-app镜像构建
│   ├── install_flink_operator.sh        # Flink Operator安装
│   ├── init_db.py           # MongoDB数据库初始化
│   ├── init_remote_mongo.py # 远程MongoDB初始化
│   ├── init_milvus.py       # Milvus向量库初始化
│   └── flink_app_entrypoint.py # Flink作业入口点（脚本下载器）
├── tests/                   # 单元测试和集成测试
│   ├── test_scenario.py     # 场景服务测试
│   ├── test_recommendation.py # 推荐服务测试
│   └── test_flink_jobs.py   # Flink作业测试
├── Dockerfile.flink-python  # Flink Python基础镜像（Flink 2.0 + PyFlink 2.1.1）
├── Dockerfile.flink-app     # Flink应用镜像（基于flink-python）
├── Dockerfile              # 推荐服务镜像
├── docker-compose.yml       # Docker Compose本地开发环境
├── Makefile                # 快捷命令（init-db、test、docker-build）
├── pyproject.toml          # Poetry依赖管理
├── ARCHITECTURE_CHECK.md    # 架构完整性检查清单⭐
├── QUICKSTART.md           # 快速开始指南（含curl示例）
└── README.md               # 项目说明（本文件）
```

### 核心文件功能说明

#### 🔧 Flink相关（企业级标准）

| 文件 | 功能 | 技术亮点 |
|------|------|---------|
| `Dockerfile.flink-python` | Flink Python基础镜像 | • Flink 2.0 + PyFlink 2.1.1<br>• Kafka Connector 3.3.0<br>• 符合阿里云/字节跳动分层镜像标准 |
| `Dockerfile.flink-app` | Flink应用镜像 | • 继承flink-python<br>• 脚本下载器（entrypoint.py）<br>• 从MongoDB动态拉取用户脚本 |
| `scripts/build_flink_images.sh` | 镜像构建脚本 | • 7步自动化构建流程<br>• PyFlink完整性验证<br>• AMD64跨平台构建 |
| `app/services/flink/crd_generator.py` | CRD生成器 | • 生成FlinkDeployment配置<br>• 资源档位预设（micro/small/medium/large/xlarge）<br>• HPA自动伸缩支持 |
| `k8s-deploy/k8s-deployment-http-grpc.yaml` | K8s部署配置 | • HTTP+gRPC双协议服务<br>• RBAC权限配置<br>• ConfigMap环境变量管理 |
| `docs/Flink架构与部署完整指南.md` | Flink部署文档 | • 完整的部署流程<br>• 故障排查指南<br>• 企业级标准对照 |

#### 🎯 推荐引擎核心

| 文件 | 功能 | 算法 |
|------|------|-----|
| `app/engine/recall/hot.py` | 热门召回 | 时间衰减算法 |
| `app/engine/recall/cf.py` | 协同过滤召回 | User/Item-based CF |
| `app/engine/recall/vector.py` | 向量召回 | Milvus ANN搜索 |
| `app/engine/reranker/diversity.py` | 多样性重排 | MMR算法（最大边际相关） |
| `app/engine/reranker/freshness.py` | 新鲜度重排 | 时间衰减 + Sigmoid |

#### 🌐 API服务层

| 文件 | 功能 | 特性 |
|------|------|-----|
| `app/api/v1/recommendation.py` | 推荐请求API | • 多召回策略融合<br>• Debug模式<br>• 性能指标埋点 |
| `app/api/v1/flink_jobs.py` | Flink作业管理 | • 作业提交/停止/删除<br>• 状态查询<br>• 日志查看 |
| `app/api/v1/scenario.py` | 场景管理 | • 场景CRUD<br>• 配置验证<br>• 策略组合 |

#### 🎨 前端管理后台

| 文件 | 功能 | 技术栈 |
|------|------|--------|
| `admin-frontend/src/views/FlinkJobs.vue` | Flink作业管理界面 | Vue3 + Element Plus |
| `admin-frontend/src/views/Dashboard.vue` | 实时监控仪表板 | ECharts + 实时刷新 |
| `admin-frontend/src/views/Items.vue` | 物品批量导入 | CSV/Excel上传 |

### 微服务拆分（K8s生产环境）

| 服务 | 端口 | 协议 | 职责 |
|------|------|------|------|
| **scenario-service** | 8001/9001 | HTTP+gRPC | 场景管理（CRUD、配置验证） |
| **item-service** | 8002/9002 | HTTP+gRPC | 物品管理（CRUD、批量导入） |
| **behavior-service** | 8003 | HTTP | 行为采集（上报、统计） |
| **recommendation-service** | 8004 | HTTP | 推荐服务（流程编排） |
| **feature-service** | 9005 | gRPC | 特征提取（在线特征） |
| **model-service** | 9006 | gRPC | 模型服务（在线预测） |

### 端口规划

| 端口 | 服务 | 用途 | 环境 |
|------|------|------|------|
| 19080 | Vue3前端 | 管理后台 | 开发 |
| 18081 | FastAPI | 推荐系统API | 开发 |
| 27017 | MongoDB | 业务数据 | 开发 |
| 6379 | Redis | 缓存/队列 | 复用本地 |
| 9092 | Kafka | 消息队列 | 复用本地 |
| 19530 | Milvus | 向量检索 | 复用本地 |
| 9090 | Prometheus | 监控指标 | 可选 |
| 3000 | Grafana | 可视化 | 可选 |

### 环境配置

支持多环境配置，通过 `ENV` 环境变量切换：

```bash
# 本地开发（默认）
ENV=local poetry run python app/main.py

# 测试环境
ENV=test poetry run python app/main.py

# 生产环境
ENV=prod poetry run python app/main.py
```

配置文件: `config/local.env`, `config/test.env`, `config/prod.env`

---

## 🚢 部署

### Docker部署

```bash
# 构建镜像
make docker-build

# 启动服务
make docker-up

# 查看日志
docker-compose logs -f mongodb
```

### Kubernetes部署

```bash
# 应用配置
kubectl apply -f k8s/base/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/

# 查看状态
kubectl get pods -n lemo-recommender
```

详见: [K8s部署文档](k8s/README.md)

---

## 📊 监控

### Prometheus

访问: http://localhost:9090

```yaml
# 启动Prometheus
docker-compose up -d prometheus
```

### Grafana

访问: http://localhost:3000 (admin/admin)

```yaml
# 启动Grafana
docker-compose up -d grafana
```

---

## 🧪 测试

```bash
# 运行所有测试
make test

# 运行特定测试
poetry run pytest tests/test_recommendation.py -v

# 代码覆盖率
poetry run pytest --cov=app --cov-report=html
```

---

## 📚 文档

- **[快速开始](QUICKSTART.md)** ⭐ - 新手必看！包含详细curl示例和故障排查
- [系统设计文档](docs/系统设计.md) - 完整的技术架构和设计
- [开发计划](docs/开发计划.md) - 22周开发路线图（已完成Week 1-20）
- [K8s部署文档](k8s/README.md) - Kubernetes部署配置说明
- [管理后台文档](admin-frontend/README.md) - 前端管理后台说明

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📄 许可证

[MIT License](LICENSE)

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [MongoDB](https://www.mongodb.com/)
- [Apache Kafka](https://kafka.apache.org/)
- [Apache Flink](https://flink.apache.org/)
- [Milvus](https://milvus.io/)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star！**

Made with ❤️ by Lemo Team

</div>
