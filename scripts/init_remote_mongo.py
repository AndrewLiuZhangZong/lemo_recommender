#!/usr/bin/env python3
"""
MongoDB 远程初始化脚本
连接到服务器 MongoDB 并创建数据库、集合、索引和用户
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime

# MongoDB 连接配置
MONGO_HOST = "111.228.39.41"
MONGO_PORT = 27017
MONGO_ADMIN_USER = "admin"
MONGO_ADMIN_PASSWORD = "password"
MONGO_DB_NAME = "lemo_recommender"
MONGO_APP_USER = "lemo_user"
MONGO_APP_PASSWORD = "lemo_password_2024"

def init_mongodb():
    # 连接到 MongoDB
    print(f"正在连接到 MongoDB: {MONGO_HOST}:{MONGO_PORT}...")
    client = MongoClient(
        host=MONGO_HOST,
        port=MONGO_PORT,
        username=MONGO_ADMIN_USER,
        password=MONGO_ADMIN_PASSWORD,
        authSource="admin"
    )
    
    # 切换到目标数据库
    db = client[MONGO_DB_NAME]
    
    print(f"开始初始化数据库: {MONGO_DB_NAME}")
    
    # 创建应用用户
    try:
        db.command("createUser", MONGO_APP_USER, 
                   pwd=MONGO_APP_PASSWORD,
                   roles=[{"role": "readWrite", "db": MONGO_DB_NAME}])
        print(f"✓ 用户创建成功: {MONGO_APP_USER}")
    except Exception as e:
        if "already exists" in str(e):
            print(f"⚠ 用户已存在: {MONGO_APP_USER}")
        else:
            print(f"✗ 创建用户失败: {e}")
    
    # 创建集合
    collections = [
        'scenarios', 'items', 'users', 'interactions',
        'experiments', 'models', 'analytics', 'audit_logs'
    ]
    
    for coll_name in collections:
        if coll_name not in db.list_collection_names():
            db.create_collection(coll_name)
            print(f"✓ 集合创建成功: {coll_name}")
        else:
            print(f"⚠ 集合已存在: {coll_name}")
    
    # 创建索引
    print("\n开始创建索引...")
    
    # scenarios 索引
    db.scenarios.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING)], unique=True)
    db.scenarios.create_index([("tenant_id", ASCENDING), ("status", ASCENDING)])
    db.scenarios.create_index([("created_at", DESCENDING)])
    print("✓ scenarios 索引创建完成")
    
    # items 索引
    db.items.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("item_id", ASCENDING)], unique=True)
    db.items.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("status", ASCENDING)])
    db.items.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("category", ASCENDING)])
    db.items.create_index([("created_at", DESCENDING)])
    db.items.create_index([("updated_at", DESCENDING)])
    print("✓ items 索引创建完成")
    
    # users 索引
    db.users.create_index([("tenant_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
    db.users.create_index([("created_at", DESCENDING)])
    print("✓ users 索引创建完成")
    
    # interactions 索引
    db.interactions.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("user_id", ASCENDING)])
    db.interactions.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("item_id", ASCENDING)])
    db.interactions.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("action_type", ASCENDING)])
    db.interactions.create_index([("timestamp", DESCENDING)])
    db.interactions.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("timestamp", DESCENDING)])
    print("✓ interactions 索引创建完成")
    
    # experiments 索引
    db.experiments.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("experiment_id", ASCENDING)], unique=True)
    db.experiments.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("status", ASCENDING)])
    db.experiments.create_index([("start_time", DESCENDING)])
    print("✓ experiments 索引创建完成")
    
    # models 索引
    db.models.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("model_id", ASCENDING)], unique=True)
    db.models.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("model_type", ASCENDING)])
    db.models.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("status", ASCENDING)])
    db.models.create_index([("version", DESCENDING)])
    db.models.create_index([("created_at", DESCENDING)])
    print("✓ models 索引创建完成")
    
    # analytics 索引
    db.analytics.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("date", DESCENDING)])
    db.analytics.create_index([("tenant_id", ASCENDING), ("scenario_id", ASCENDING), ("metric_type", ASCENDING), ("date", DESCENDING)])
    print("✓ analytics 索引创建完成")
    
    # audit_logs 索引
    db.audit_logs.create_index([("tenant_id", ASCENDING), ("timestamp", DESCENDING)])
    db.audit_logs.create_index([("operator", ASCENDING), ("timestamp", DESCENDING)])
    db.audit_logs.create_index([("action", ASCENDING), ("timestamp", DESCENDING)])
    db.audit_logs.create_index([("resource_type", ASCENDING), ("resource_id", ASCENDING)])
    print("✓ audit_logs 索引创建完成")
    
    # 插入测试数据
    print("\n插入测试数据...")
    test_scenario = {
        "tenant_id": "test_tenant",
        "scenario_id": "homepage_recommend",
        "name": "首页推荐",
        "description": "首页个性化推荐场景",
        "config": {
            "algorithm": "collaborative_filtering",
            "recall_size": 100,
            "rank_size": 20
        },
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    try:
        db.scenarios.insert_one(test_scenario)
        print("✓ 测试数据插入成功")
    except Exception as e:
        if "duplicate key" in str(e):
            print("⚠ 测试数据已存在")
        else:
            print(f"✗ 插入测试数据失败: {e}")
    
    # 关闭连接
    client.close()
    
    print("\n" + "="*50)
    print("MongoDB 初始化完成！")
    print("="*50)
    print(f"\n连接信息:")
    print(f"  主机: {MONGO_HOST}:{MONGO_PORT}")
    print(f"  数据库: {MONGO_DB_NAME}")
    print(f"  应用用户: {MONGO_APP_USER}")
    print(f"  应用密码: {MONGO_APP_PASSWORD}")
    print(f"\n连接字符串:")
    print(f"  mongodb://{MONGO_APP_USER}:{MONGO_APP_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}")

if __name__ == "__main__":
    try:
        init_mongodb()
    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()

