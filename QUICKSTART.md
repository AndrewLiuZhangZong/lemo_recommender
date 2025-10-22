# 🚀 快速开始指南

## 环境要求

- Python 3.10+
- Node.js 18+
- MongoDB 6.0+
- Redis 7+
- Docker & Docker Compose (可选)

## 1. 后端启动

### 方式一：使用Poetry（推荐）

```bash
# 安装依赖
poetry install

# 启动MongoDB（如果没有运行）
docker-compose up -d mongodb

# 初始化数据库
poetry run python scripts/init_db.py

# 启动API服务
ENV=local poetry run python app/main.py
```

访问：
- API文档: http://localhost:8080/api/v1/docs
- 健康检查: http://localhost:8080/health

### 方式二：使用Docker Compose

```bash
docker-compose up -d
```

## 2. 前端启动

```bash
# 进入前端目录
cd admin-frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问: http://localhost:3000

## 3. 快速测试

### 创建场景

```bash
curl -X POST "http://localhost:8080/api/v1/scenarios" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: demo_tenant" \
  -H "X-User-Id: admin" \
  -d '{
    "scenario_id": "vlog_main_feed",
    "tenant_id": "demo_tenant",
    "name": "短视频主信息流",
    "scenario_type": "vlog",
    "description": "抖音式短视频推荐场景",
    "config": {
      "recall_strategies": [
        {"name": "hot_items", "weight": 0.3},
        {"name": "collaborative_filtering", "weight": 0.4},
        {"name": "vector_search", "weight": 0.3}
      ]
    }
  }'
```

### 导入物品

```bash
curl -X POST "http://localhost:8080/api/v1/items/batch" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: demo_tenant" \
  -H "X-User-Id: admin" \
  -d '{
    "items": [
      {
        "item_id": "vlog_001",
        "tenant_id": "demo_tenant",
        "scenario_id": "vlog_main_feed",
        "metadata": {
          "title": "旅行vlog - 三亚海边",
          "category": "travel",
          "author": "旅行达人",
          "duration": 180,
          "tags": ["旅行", "海边", "三亚"]
        }
      }
    ]
  }'
```

### 获取推荐

```bash
curl -X POST "http://localhost:8080/api/v1/recommend" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: demo_tenant" \
  -H "X-User-Id: user_001" \
  -d '{
    "scenario_id": "vlog_main_feed",
    "user_id": "user_001",
    "limit": 20,
    "context": {
      "device": "mobile",
      "location": "beijing"
    }
  }'
```

## 4. 使用管理后台

1. 打开 http://localhost:3000
2. 进入"场景管理"创建场景
3. 进入"物品管理"导入物品数据
4. 进入"仪表板"查看数据统计
5. 进入"AB实验"创建实验

## 5. 可选组件启动

### Celery Worker (离线任务)

```bash
celery -A app.tasks.celery_app worker -l info
```

### Celery Beat (定时任务)

```bash
celery -A app.tasks.celery_app beat -l info
```

### Flink作业 (实时计算)

```bash
# 用户画像实时更新
python flink_jobs/user_profile_updater.py

# 物品热度计算
python flink_jobs/item_hot_score_calculator.py

# 实时指标统计
python flink_jobs/recommendation_metrics.py
```

## 6. 监控查看

### Prometheus指标

访问: http://localhost:8080/metrics

### Grafana Dashboard

1. 启动Grafana: `docker-compose up -d grafana`
2. 访问: http://localhost:3001
3. 默认账号: admin/admin
4. 导入Dashboard配置

## 常见问题

### Q: MongoDB连接失败？
A: 检查MongoDB是否启动，端口是否正确（默认27017）

### Q: 前端API调用失败？
A: 检查后端是否启动，CORS是否配置正确

### Q: Celery任务不执行？
A: 检查Redis是否启动，Kafka是否运行

### Q: 推荐结果为空？
A: 确保已创建场景和物品数据

## 下一步

- 查看 [系统设计文档](docs/系统设计.md)
- 查看 [开发计划](docs/开发计划.md)
- 查看 [API文档](http://localhost:8080/api/v1/docs)

## 技术支持

- GitHub Issues: https://github.com/AndrewLiuZhangZong/lemo_recommender/issues
- API文档: http://localhost:8080/api/v1/docs
