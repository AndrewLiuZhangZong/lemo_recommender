#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


async def create_indexes():
    """创建MongoDB索引"""
    
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_database]
    
    print("📚 创建MongoDB索引...")
    
    # scenarios集合索引
    await db.scenarios.create_index([("tenant_id", 1), ("scenario_id", 1)], unique=True)
    await db.scenarios.create_index([("tenant_id", 1), ("status", 1)])
    print("✅ scenarios索引创建完成")
    
    # items集合索引
    await db.items.create_index([("tenant_id", 1), ("scenario_id", 1), ("item_id", 1)], unique=True)
    await db.items.create_index([("tenant_id", 1), ("scenario_id", 1), ("status", 1)])
    await db.items.create_index([("metadata.category", 1)])
    await db.items.create_index([("metadata.tags", 1)])
    print("✅ items索引创建完成")
    
    # user_profiles集合索引
    await db.user_profiles.create_index([("tenant_id", 1), ("user_id", 1), ("scenario_id", 1)], unique=True)
    await db.user_profiles.create_index([("tenant_id", 1), ("user_id", 1)])
    print("✅ user_profiles索引创建完成")
    
    # interactions集合索引
    await db.interactions.create_index([("tenant_id", 1), ("user_id", 1), ("timestamp", -1)])
    await db.interactions.create_index([("tenant_id", 1), ("item_id", 1), ("timestamp", -1)])
    await db.interactions.create_index([("tenant_id", 1), ("scenario_id", 1), ("timestamp", -1)])
    await db.interactions.create_index([("timestamp", -1)])
    print("✅ interactions索引创建完成")
    
    # model_configs集合索引
    await db.model_configs.create_index([("scenario_id", 1), ("model_type", 1)])
    await db.model_configs.create_index([("status", 1)])
    print("✅ model_configs索引创建完成")
    
    # experiments集合索引
    await db.experiments.create_index([("tenant_id", 1), ("scenario_id", 1)])
    await db.experiments.create_index([("status", 1)])
    print("✅ experiments索引创建完成")
    
    client.close()
    print("\n🎉 所有索引创建完成！")


async def create_sample_data():
    """创建示例数据"""
    
    from datetime import datetime
    from app.models.scenario import ScenarioType, ScenarioStatus, ScenarioConfig, RecallStrategyConfig, RankConfig
    
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_database]
    
    print("\n📝 创建示例数据...")
    
    # 示例场景
    sample_scenario = {
        "tenant_id": "demo_tenant",
        "scenario_id": "vlog_main_feed",
        "scenario_type": "vlog",
        "name": "短视频主Feed流",
        "description": "短视频推荐主场景示例",
        "config": {
            "features": {
                "item_features": [
                    {"name": "duration", "type": "numeric", "weight": 1.0},
                    {"name": "completion_rate", "type": "numeric", "weight": 2.0},
                    {"name": "category", "type": "categorical", "weight": 1.5}
                ],
                "user_features": [
                    {"name": "age", "type": "categorical"},
                    {"name": "favorite_categories", "type": "multi_categorical"}
                ]
            },
            "recall": {
                "strategies": [
                    {"name": "user_cf", "weight": 0.3, "limit": 100},
                    {"name": "item_cf", "weight": 0.3, "limit": 100},
                    {"name": "hot_items", "weight": 0.2, "limit": 50}
                ]
            },
            "rank": {
                "model": "simple_score",
                "version": "v1.0",
                "objective": "watch_time"
            },
            "rerank": {
                "rules": [
                    {"name": "diversity", "weight": 0.3},
                    {"name": "freshness", "weight": 0.2}
                ]
            }
        },
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    existing_scenario = await db.scenarios.find_one({
        "tenant_id": "demo_tenant",
        "scenario_id": "vlog_main_feed"
    })
    
    if not existing_scenario:
        await db.scenarios.insert_one(sample_scenario)
        print("✅ 示例场景创建完成")
    else:
        print("ℹ️  示例场景已存在")
    
    # 示例物品
    sample_items = [
        {
            "tenant_id": "demo_tenant",
            "scenario_id": "vlog_main_feed",
            "item_id": f"video_{i:03d}",
            "metadata": {
                "title": f"搞笑视频{i}",
                "duration": 60 + i * 10,
                "category": ["entertainment", "sports", "tech"][i % 3],
                "tags": ["funny", "comedy", "viral"],
                "view_count": 1000 * i,
                "like_count": 100 * i,
                "completion_rate": 0.7 + (i % 10) * 0.02,
                "publish_time": datetime.utcnow().isoformat()
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        for i in range(1, 21)
    ]
    
    existing_items = await db.items.count_documents({
        "tenant_id": "demo_tenant",
        "scenario_id": "vlog_main_feed"
    })
    
    if existing_items == 0:
        await db.items.insert_many(sample_items)
        print(f"✅ 创建了{len(sample_items)}个示例物品")
    else:
        print(f"ℹ️  已存在{existing_items}个物品")
    
    client.close()
    print("\n🎉 示例数据创建完成！")


async def main():
    """主函数"""
    
    print("=" * 60)
    print("  Lemo Recommender - 数据库初始化")
    print("=" * 60)
    print()
    
    try:
        await create_indexes()
        await create_sample_data()
        
        print()
        print("=" * 60)
        print("  初始化完成！")
        print("=" * 60)
        print()
        print("🚀 现在可以启动应用了:")
        print("   poetry run python app/main.py")
        print()
        print("📖 API文档:")
        print("   http://localhost:8080/api/v1/docs")
        print()
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

