"""
数据库索引优化脚本

为MongoDB创建合适的索引，提升查询性能
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


async def optimize_indexes():
    """优化MongoDB索引"""
    
    print("=" * 60)
    print("MongoDB 索引优化脚本")
    print("=" * 60)
    
    # 连接MongoDB
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_database]
    
    print(f"\n连接到数据库: {settings.mongodb_database}")
    
    # ==================== 物品表索引 ====================
    print("\n[1/6] 优化 items 表索引...")
    
    # 索引1: 租户+场景+状态+发布时间 (用于查询最新物品)
    await db.items.create_index([
        ("tenant_id", 1),
        ("scenario_id", 1),
        ("status", 1),
        ("created_at", -1)
    ], name="idx_tenant_scenario_status_time")
    print("  ✓ 创建索引: tenant_id + scenario_id + status + created_at")
    
    # 索引2: 租户+场景+物品ID (唯一索引，用于快速查找)
    await db.items.create_index([
        ("tenant_id", 1),
        ("scenario_id", 1),
        ("item_id", 1)
    ], name="idx_tenant_scenario_item", unique=True)
    print("  ✓ 创建唯一索引: tenant_id + scenario_id + item_id")
    
    # 索引3: 租户+场景+标签 (用于标签召回)
    await db.items.create_index([
        ("tenant_id", 1),
        ("scenario_id", 1),
        ("metadata.tags", 1)
    ], name="idx_tenant_scenario_tags")
    print("  ✓ 创建索引: tenant_id + scenario_id + metadata.tags")
    
    # 索引4: 租户+场景+分类 (用于分类召回)
    await db.items.create_index([
        ("tenant_id", 1),
        ("scenario_id", 1),
        ("metadata.category", 1)
    ], name="idx_tenant_scenario_category")
    print("  ✓ 创建索引: tenant_id + scenario_id + metadata.category")
    
    # ==================== 用户画像表索引 ====================
    print("\n[2/6] 优化 user_profiles 表索引...")
    
    # 索引1: 租户+用户ID+场景 (唯一索引)
    await db.user_profiles.create_index([
        ("tenant_id", 1),
        ("user_id", 1),
        ("scenario_id", 1)
    ], name="idx_tenant_user_scenario", unique=True)
    print("  ✓ 创建唯一索引: tenant_id + user_id + scenario_id")
    
    # 索引2: 租户+场景+更新时间 (用于查询活跃用户)
    await db.user_profiles.create_index([
        ("tenant_id", 1),
        ("scenario_id", 1),
        ("updated_at", -1)
    ], name="idx_tenant_scenario_update_time")
    print("  ✓ 创建索引: tenant_id + scenario_id + updated_at")
    
    # ==================== 场景配置表索引 ====================
    print("\n[3/6] 优化 scenarios 表索引...")
    
    # 索引1: 租户+场景ID (唯一索引)
    await db.scenarios.create_index([
        ("tenant_id", 1),
        ("scenario_id", 1)
    ], name="idx_tenant_scenario", unique=True)
    print("  ✓ 创建唯一索引: tenant_id + scenario_id")
    
    # 索引2: 租户+状态 (用于查询活跃场景)
    await db.scenarios.create_index([
        ("tenant_id", 1),
        ("status", 1)
    ], name="idx_tenant_status")
    print("  ✓ 创建索引: tenant_id + status")
    
    # ==================== 模型配置表索引 ====================
    print("\n[4/6] 优化 model_configs 表索引...")
    
    # 索引1: 租户+场景+模型类型
    await db.model_configs.create_index([
        ("tenant_id", 1),
        ("scenario_id", 1),
        ("model_type", 1)
    ], name="idx_tenant_scenario_model_type")
    print("  ✓ 创建索引: tenant_id + scenario_id + model_type")
    
    # 索引2: 租户+场景+版本+状态 (用于查询活跃版本)
    await db.model_configs.create_index([
        ("tenant_id", 1),
        ("scenario_id", 1),
        ("version", -1),
        ("status", 1)
    ], name="idx_tenant_scenario_version_status")
    print("  ✓ 创建索引: tenant_id + scenario_id + version + status")
    
    # ==================== 实验配置表索引 ====================
    print("\n[5/6] 优化 experiments 表索引...")
    
    # 索引1: 租户+场景+状态
    await db.experiments.create_index([
        ("tenant_id", 1),
        ("scenario_id", 1),
        ("status", 1)
    ], name="idx_tenant_scenario_status")
    print("  ✓ 创建索引: tenant_id + scenario_id + status")
    
    # 索引2: 租户+实验ID (唯一索引)
    await db.experiments.create_index([
        ("tenant_id", 1),
        ("experiment_id", 1)
    ], name="idx_tenant_experiment", unique=True)
    print("  ✓ 创建唯一索引: tenant_id + experiment_id")
    
    # ==================== 场景跟踪模板表索引 ====================
    print("\n[6/6] 优化 scenario_tracking_templates 表索引...")
    
    # 索引1: 租户+场景+模板类型
    await db.scenario_tracking_templates.create_index([
        ("tenant_id", 1),
        ("scenario_id", 1),
        ("template_type", 1)
    ], name="idx_tenant_scenario_template_type")
    print("  ✓ 创建索引: tenant_id + scenario_id + template_type")
    
    # ==================== 查看索引信息 ====================
    print("\n" + "=" * 60)
    print("索引创建完成！")
    print("=" * 60)
    
    # 显示各表的索引信息
    collections = [
        "items",
        "user_profiles",
        "scenarios",
        "model_configs",
        "experiments",
        "scenario_tracking_templates"
    ]
    
    print("\n索引汇总:")
    for coll_name in collections:
        indexes = await db[coll_name].index_information()
        print(f"\n{coll_name} ({len(indexes)} 个索引):")
        for idx_name, idx_info in indexes.items():
            if idx_name == "_id_":
                continue
            keys = idx_info.get("key", [])
            unique = "唯一" if idx_info.get("unique", False) else "普通"
            print(f"  - {idx_name} ({unique}): {keys}")
    
    # 关闭连接
    client.close()
    print("\n✅ 数据库连接已关闭")


async def drop_unused_indexes():
    """删除不再使用的索引"""
    
    print("\n" + "=" * 60)
    print("清理无用索引")
    print("=" * 60)
    
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_database]
    
    # 这里可以添加需要删除的索引
    # 示例:
    # await db.items.drop_index("old_index_name")
    
    print("\n✅ 无用索引清理完成")
    client.close()


async def analyze_slow_queries():
    """分析慢查询"""
    
    print("\n" + "=" * 60)
    print("慢查询分析")
    print("=" * 60)
    
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_database]
    
    # 启用分析器 (仅记录慢查询，阈值100ms)
    await db.command("profile", 1, slowms=100)
    
    # 查询最近的慢查询
    cursor = db.system.profile.find().sort("ts", -1).limit(10)
    
    print("\n最近10条慢查询:")
    async for query in cursor:
        print(f"\n耗时: {query.get('millis', 0)}ms")
        print(f"集合: {query.get('ns', 'N/A')}")
        print(f"操作: {query.get('op', 'N/A')}")
        if 'command' in query:
            print(f"命令: {query['command']}")
    
    # 关闭分析器
    await db.command("profile", 0)
    
    client.close()
    print("\n✅ 慢查询分析完成")


async def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "optimize":
            await optimize_indexes()
        elif action == "clean":
            await drop_unused_indexes()
        elif action == "analyze":
            await analyze_slow_queries()
        else:
            print(f"未知操作: {action}")
            print("用法: python scripts/optimize_indexes.py [optimize|clean|analyze]")
    else:
        # 默认执行优化
        await optimize_indexes()


if __name__ == "__main__":
    asyncio.run(main())

