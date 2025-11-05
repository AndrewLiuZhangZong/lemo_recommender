"""
缓存预热服务

定期预热热数据到缓存，提升命中率
"""
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta


class CacheWarmer:
    """
    缓存预热器
    
    功能：
    1. 定期预热热门物品
    2. 预热活跃用户画像
    3. 智能预测需要预热的数据
    """
    
    def __init__(
        self,
        db,
        redis_client,
        multi_level_cache
    ):
        self.db = db
        self.redis = redis_client
        self.cache = multi_level_cache
        self.running = False
    
    async def start_warming(self, interval_seconds: int = 300):
        """
        启动缓存预热（每5分钟）
        
        Args:
            interval_seconds: 预热间隔（秒）
        """
        self.running = True
        print(f"[CacheWarmer] 启动，预热间隔: {interval_seconds}秒")
        
        while self.running:
            try:
                await self.warm_all()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                print(f"[CacheWarmer] 预热失败: {e}")
                await asyncio.sleep(60)  # 失败后等待1分钟重试
    
    def stop_warming(self):
        """停止缓存预热"""
        self.running = False
        print("[CacheWarmer] 已停止")
    
    async def warm_all(self):
        """执行一次完整预热"""
        print(f"[CacheWarmer] 开始预热 - {datetime.now()}")
        start_time = datetime.now()
        
        # 并行预热
        results = await asyncio.gather(
            self.warm_hot_items(),
            self.warm_active_users(),
            return_exceptions=True
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"[CacheWarmer] 预热完成，耗时: {elapsed:.2f}秒")
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[CacheWarmer] 预热任务{i}失败: {result}")
    
    async def warm_hot_items(self):
        """预热热门物品"""
        print("[CacheWarmer] 预热热门物品...")
        
        # 从MongoDB统计最近1天的热门物品
        pipeline = [
            {
                "$match": {
                    "created_at": {
                        "$gte": datetime.utcnow() - timedelta(days=1)
                    },
                    "status": "active"
                }
            },
            {
                "$group": {
                    "_id": {
                        "tenant_id": "$tenant_id",
                        "scenario_id": "$scenario_id"
                    },
                    "items": {
                        "$push": {
                            "item_id": "$item_id",
                            "metadata": "$metadata"
                        }
                    }
                }
            },
            {"$limit": 10}  # 最多处理10个场景
        ]
        
        cursor = self.db.items.aggregate(pipeline)
        
        warmed_count = 0
        async for doc in cursor:
            tenant_id = doc["_id"]["tenant_id"]
            scenario_id = doc["_id"]["scenario_id"]
            items = doc["items"][:100]  # 每个场景预热前100个物品
            
            # 写入L3缓存
            items_dict = {
                item["item_id"]: item["metadata"]
                for item in items
            }
            await self.cache.set_items_cache_batch(items_dict)
            
            # 计算热度分并写入L2
            item_scores = {
                item["item_id"]: 100.0  # 简单实现，后续可以基于CTR等指标
                for item in items
            }
            await self.cache.update_hot_items(scenario_id, item_scores)
            
            warmed_count += len(items)
        
        print(f"[CacheWarmer] 预热热门物品完成: {warmed_count}个")
        return warmed_count
    
    async def warm_active_users(self):
        """预热活跃用户画像"""
        print("[CacheWarmer] 预热活跃用户...")
        
        # 从Redis获取最近活跃的用户列表
        # 假设有个活跃用户ZSET: active_users
        try:
            # 获取最近1小时活跃的top 1000用户
            active_users = await self.redis.zrevrange(
                "active_users",
                0,
                999
            )
            
            if not active_users:
                print("[CacheWarmer] 没有活跃用户")
                return 0
            
            # 从MongoDB批量查询用户画像
            user_ids = [
                user.decode() if isinstance(user, bytes) else user
                for user in active_users
            ]
            
            cursor = self.db.user_profiles.find({
                "user_id": {"$in": user_ids}
            })
            
            warmed_count = 0
            async for profile in cursor:
                user_id = profile["user_id"]
                
                # 写入L2缓存
                await self.cache.set_user_profile_cache(
                    user_id=user_id,
                    profile={
                        "user_id": user_id,
                        "preferences": profile.get("preferences", {}),
                        "tags": profile.get("tags", []),
                        "metadata": profile.get("metadata", {})
                    }
                )
                warmed_count += 1
            
            print(f"[CacheWarmer] 预热用户画像完成: {warmed_count}个")
            return warmed_count
            
        except Exception as e:
            print(f"[CacheWarmer] 预热用户画像失败: {e}")
            return 0
    
    async def warm_scenario_items(
        self,
        tenant_id: str,
        scenario_id: str,
        limit: int = 200
    ):
        """
        为特定场景预热物品
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            limit: 预热数量
        """
        cursor = self.db.items.find({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "status": "active"
        }).sort("created_at", -1).limit(limit)
        
        warmed = 0
        async for item in cursor:
            await self.cache.set_item_cache(
                item_id=item["item_id"],
                item_data={
                    "item_id": item["item_id"],
                    "metadata": item.get("metadata", {}),
                    "embedding": item.get("embedding")
                }
            )
            warmed += 1
        
        return warmed

