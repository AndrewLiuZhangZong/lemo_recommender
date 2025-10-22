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
- **⚡ 高性能**: FastAPI异步框架 + MongoDB + Redis
- **📊 实时计算**: Kafka + Flink实时特征计算
- **☸️ 云原生**: 支持Docker和Kubernetes部署
- **📈 可观测**: Prometheus + Grafana监控体系

---

## 🚀 功能特性

### 推荐引擎

| 模块 | 功能 | 状态 |
|------|------|-----|
| **召回层** | 协同过滤、向量召回、热门召回 | ✅ |
| **排序层** | LightGBM、DeepFM、Wide&Deep | 🚧 |
| **重排层** | 多样性、新鲜度、业务规则 | ✅ |

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

### 环境要求

- Python 3.10+
- Docker & Docker Compose
- **本项目启动**: MongoDB 4.4+
- **使用本地已有服务**:
  - Redis 6.0+
  - Kafka 3.0+
  - Milvus 2.4+ (第二阶段)

### 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/your-org/lemo_recommender.git
cd lemo_recommender

# 2. 快速启动（自动安装依赖、启动MongoDB、初始化数据库）
make quick-start

# 访问API文档: http://localhost:8080/api/v1/docs
```

### 手动启动

```bash
# 1. 安装依赖
poetry install

# 2. 配置环境变量
cp .env.example .env

# 3. 启动MongoDB（Redis和Kafka使用本地已有）
docker-compose up -d mongodb

# 4. 初始化数据库
make init-db

# 5. 启动应用
make start
```

---

## 📡 API文档

启动后访问: **http://localhost:8080/api/v1/docs**

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
BASE_URL = "http://localhost:8080/api/v1"
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

## 🏗️ 项目架构

### 整体结构

```
lemo_recommender/
├── app/                    # 应用主目录
│   ├── models/            # 数据模型层（Pydantic）
│   ├── services/          # 业务逻辑层
│   │   ├── scenario/      # 场景管理
│   │   ├── item/          # 物品管理
│   │   ├── interaction/   # 行为采集
│   │   └── recommendation/ # 推荐服务
│   ├── engine/            # 推荐引擎
│   │   ├── recall/        # 召回策略（协同过滤、热门、向量）
│   │   ├── ranker/        # 排序模型
│   │   └── reranker/      # 重排规则（多样性、新鲜度）
│   ├── api/v1/            # API路由
│   ├── grpc_clients/      # gRPC客户端（租户/用户服务）
│   └── core/              # 核心配置（数据库、Redis）
├── config/                 # 多环境配置
│   ├── local.env          # 本地开发配置
│   ├── test.env           # 测试环境配置
│   └── prod.env           # 生产环境配置
├── docs/                   # 文档
│   ├── 系统设计.md         # 完整技术架构
│   └── 开发计划.md         # 22周开发路线图
├── k8s/                   # Kubernetes部署配置
├── tests/                 # 测试
└── scripts/               # 脚本工具
```

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
| 8080 | FastAPI | 推荐系统API | 开发 |
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

- [系统设计文档](docs/系统设计.md) - 完整的技术架构和设计
- [开发计划](docs/开发计划.md) - 22周开发路线图（已完成第一阶段）
- [K8s部署文档](k8s/README.md) - Kubernetes部署配置说明

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
