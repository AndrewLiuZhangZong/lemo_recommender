// MongoDB 初始化脚本 - Lemo Recommender
// 连接到服务器后执行：mongosh "mongodb://admin:password@111.228.39.41:27017/admin" < init-mongo.js

// 切换到 lemo_recommender 数据库
use lemo_recommender;

print('开始初始化 lemo_recommender 数据库...');

// 创建应用用户
db.createUser({
  user: 'lemo_user',
  pwd: 'lemo_password_2024',
  roles: [
    {
      role: 'readWrite',
      db: 'lemo_recommender'
    }
  ]
});

print('用户创建成功: lemo_user');

// 创建集合
db.createCollection('scenarios');
db.createCollection('items');
db.createCollection('users');
db.createCollection('interactions');
db.createCollection('experiments');
db.createCollection('models');
db.createCollection('analytics');
db.createCollection('audit_logs');

print('集合创建成功');

// 创建索引 - scenarios
db.scenarios.createIndex({ "tenant_id": 1, "scenario_id": 1 }, { unique: true });
db.scenarios.createIndex({ "tenant_id": 1, "status": 1 });
db.scenarios.createIndex({ "created_at": -1 });

// 创建索引 - items
db.items.createIndex({ "tenant_id": 1, "scenario_id": 1, "item_id": 1 }, { unique: true });
db.items.createIndex({ "tenant_id": 1, "scenario_id": 1, "status": 1 });
db.items.createIndex({ "tenant_id": 1, "scenario_id": 1, "category": 1 });
db.items.createIndex({ "created_at": -1 });
db.items.createIndex({ "updated_at": -1 });

// 创建索引 - users
db.users.createIndex({ "tenant_id": 1, "user_id": 1 }, { unique: true });
db.users.createIndex({ "created_at": -1 });

// 创建索引 - interactions
db.interactions.createIndex({ "tenant_id": 1, "scenario_id": 1, "user_id": 1 });
db.interactions.createIndex({ "tenant_id": 1, "scenario_id": 1, "item_id": 1 });
db.interactions.createIndex({ "tenant_id": 1, "scenario_id": 1, "action_type": 1 });
db.interactions.createIndex({ "timestamp": -1 });
db.interactions.createIndex({ "tenant_id": 1, "scenario_id": 1, "timestamp": -1 });

// 创建索引 - experiments
db.experiments.createIndex({ "tenant_id": 1, "scenario_id": 1, "experiment_id": 1 }, { unique: true });
db.experiments.createIndex({ "tenant_id": 1, "scenario_id": 1, "status": 1 });
db.experiments.createIndex({ "start_time": -1 });

// 创建索引 - models
db.models.createIndex({ "tenant_id": 1, "scenario_id": 1, "model_id": 1 }, { unique: true });
db.models.createIndex({ "tenant_id": 1, "scenario_id": 1, "model_type": 1 });
db.models.createIndex({ "tenant_id": 1, "scenario_id": 1, "status": 1 });
db.models.createIndex({ "version": -1 });
db.models.createIndex({ "created_at": -1 });

// 创建索引 - analytics
db.analytics.createIndex({ "tenant_id": 1, "scenario_id": 1, "date": -1 });
db.analytics.createIndex({ "tenant_id": 1, "scenario_id": 1, "metric_type": 1, "date": -1 });

// 创建索引 - audit_logs
db.audit_logs.createIndex({ "tenant_id": 1, "timestamp": -1 });
db.audit_logs.createIndex({ "operator": 1, "timestamp": -1 });
db.audit_logs.createIndex({ "action": 1, "timestamp": -1 });
db.audit_logs.createIndex({ "resource_type": 1, "resource_id": 1 });

print('索引创建成功');

// 插入测试数据（可选）
db.scenarios.insertOne({
  tenant_id: "test_tenant",
  scenario_id: "homepage_recommend",
  name: "首页推荐",
  description: "首页个性化推荐场景",
  config: {
    algorithm: "collaborative_filtering",
    recall_size: 100,
    rank_size: 20
  },
  status: "active",
  created_at: new Date(),
  updated_at: new Date()
});

print('测试数据插入成功');
print('MongoDB 初始化完成！');
