# 项目结构说明

## 整体架构

```
lemo_recommender/
├── app/                    # 应用主目录
│   ├── models/            # 数据模型层（Pydantic）
│   ├── services/          # 业务逻辑层
│   ├── api/               # API路由层
│   ├── core/              # 核心配置（数据库、Redis、配置管理）
│   ├── engine/            # 推荐引擎（召回、排序、重排）
│   ├── utils/             # 工具函数
│   └── main.py            # FastAPI应用入口
├── docs/                   # 文档目录
├── scripts/               # 脚本工具
├── tests/                 # 测试目录
├── k8s/                   # Kubernetes部署配置
├── config/                # 外部配置文件
└── pyproject.toml         # Poetry依赖管理
```

## 服务依赖

### 本项目启动的服务
- **MongoDB** (27017): 业务数据存储

### 使用本地已有服务
- **Redis** (6379): 缓存、分布式锁、Celery队列
- **Kafka** (9092): 消息队列、行为日志流
- **Milvus** (19530): 向量数据库（第二阶段）
- **Etcd** (2379): Milvus依赖
- **MinIO** (9000/8001): Milvus对象存储
- **Attu** (8000): Milvus管理界面

### 可选服务
- **Prometheus** (9090): 监控指标
- **Grafana** (3000): 可视化面板

## 端口规划

| 端口 | 服务 | 用途 | 来源 |
|------|------|------|------|
| 8080 | FastAPI | 推荐系统API | 本项目 |
| 27017 | MongoDB | 数据库 | 本项目 |
| 6379 | Redis | 缓存 | 本地已有 |
| 9092 | Kafka | 消息队列 | 本地已有 |
| 19530 | Milvus | 向量DB(gRPC) | 本地已有 |
| 9091 | Milvus | 向量DB(HTTP) | 本地已有 |
| 2379 | Etcd | 元数据存储 | 本地已有 |
| 9000 | MinIO | 对象存储API | 本地已有 |
| 8001 | MinIO | 管理控制台 | 本地已有 |
| 8000 | Attu | Milvus管理 | 本地已有 |
| 9090 | Prometheus | 监控 | 本项目(可选) |
| 3000 | Grafana | 可视化 | 本项目(可选) |

## 微服务拆分（K8s部署）

生产环境将拆分为6个独立服务：

1. **scenario-service** (8001/9001): 场景管理
2. **item-service** (8002/9002): 物品管理
3. **behavior-service** (8003): 行为采集
4. **recommendation-service** (8004): 推荐服务
5. **feature-service** (9005): 特征服务
6. **model-service** (9006): 模型服务

## 开发环境快速开始

```bash
# 1. 确认本地服务运行
docker ps | grep -E "ai_lemo_redis|ad-mat-aegis-kafka|ai_lemo_milvus"

# 2. 启动MongoDB
docker-compose up -d mongodb

# 3. 安装依赖
poetry install

# 4. 配置环境变量
cp .env.example .env

# 5. 启动应用
poetry run python app/main.py
```

访问: http://localhost:8080/api/v1/docs
