// MongoDB初始化脚本
db = db.getSiblingDB('lemo_recommender');

// 创建集合和索引

// 1. scenarios（场景配置）
db.createCollection('scenarios');
db.scenarios.createIndex({ tenant_id: 1, scenario_id: 1 }, { unique: true });
db.scenarios.createIndex({ tenant_id: 1, status: 1 });

// 2. items（物品）
db.createCollection('items');
db.items.createIndex({ tenant_id: 1, scenario_id: 1, item_id: 1 }, { unique: true });
db.items.createIndex({ tenant_id: 1, scenario_id: 1, status: 1 });
db.items.createIndex({ 'metadata.category': 1 });
db.items.createIndex({ 'metadata.publish_time': -1 });

// 3. user_profiles（用户画像）
db.createCollection('user_profiles');
db.user_profiles.createIndex({ tenant_id: 1, user_id: 1, scenario_id: 1 }, { unique: true });
db.user_profiles.createIndex({ tenant_id: 1, scenario_id: 1, updated_at: -1 });

// 4. interactions（行为日志）
db.createCollection('interactions');
db.interactions.createIndex({ tenant_id: 1, user_id: 1, timestamp: -1 });
db.interactions.createIndex({ tenant_id: 1, item_id: 1, timestamp: -1 });
db.interactions.createIndex({ tenant_id: 1, scenario_id: 1, action_type: 1, timestamp: -1 });
db.interactions.createIndex({ timestamp: -1 });

// 5. model_configs（模型配置）
db.createCollection('model_configs');
db.model_configs.createIndex({ scenario_id: 1, model_type: 1, status: 1 });

// 6. experiments（AB实验）
db.createCollection('experiments');
db.experiments.createIndex({ tenant_id: 1, scenario_id: 1, status: 1 });
db.experiments.createIndex({ experiment_id: 1 }, { unique: true });

print('✅ MongoDB初始化完成！');
print('已创建集合：scenarios, items, user_profiles, interactions, model_configs, experiments');

