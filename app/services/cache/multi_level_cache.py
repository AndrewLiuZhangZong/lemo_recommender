"""
多级缓存服务

L1: 推荐结果缓存 - TTL: 5分钟，命中率目标: 40%
L2: 热数据缓存 - TTL: 1小时，命中率目标: 50%  
L3: 物品详情缓存 - TTL: 24小时，命中率目标: 90%
"""
import json
import hashlib
from typing import Optional, List, Dict, Any, Union
from datetime import timedelta
import asyncio


class MultiLevelCache:
    """
    多级缓存管理器
    
    特点：
    1. 三级缓存架构，逐级查找
    2. 自动预热热数据
    3. 智能失效策略
    4. 性能监控
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        
        # 缓存配置
        self.cache_config = {
            "L1": {
                "prefix": "rec:",
                "ttl": 300,  # 5分钟
                "description": "推荐结果缓存"
            },
            "L2": {
                "prefix": "hot:",
                "ttl": 3600,  # 1小时
                "description": "热数据缓存"
            },
            "L3": {
                "prefix": "item:",
                "ttl": 86400,  # 24小时
                "description": "物品详情缓存"
            }
        }
        
        # 统计信息
        self.stats = {
            "L1_hits": 0,
            "L1_misses": 0,
            "L2_hits": 0,
            "L2_misses": 0,
            "L3_hits": 0,
            "L3_misses": 0
        }
    
    # ==================== L1: 推荐结果缓存 ====================
    
    def _get_recommendation_cache_key(
        self,
        scenario_id: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> str:
        """
        生成推荐结果缓存Key
        
        Key格式: rec:{scenario}:{user_id}:{context_hash}
        """
        # 对context进行排序和哈希，确保相同context生成相同key
        context_str = json.dumps(context, sort_keys=True)
        context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
        
        return f"rec:{scenario_id}:{user_id}:{context_hash}"
    
    async def get_recommendation_cache(
        self,
        scenario_id: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """获取推荐结果缓存（L1）"""
        key = self._get_recommendation_cache_key(scenario_id, user_id, context)
        
        try:
            cached = await self.redis.get(key)
            if cached:
                self.stats["L1_hits"] += 1
                return json.loads(cached)
            else:
                self.stats["L1_misses"] += 1
                return None
        except Exception as e:
            print(f"[L1 Cache] 读取失败: {e}")
            return None
    
    async def set_recommendation_cache(
        self,
        scenario_id: str,
        user_id: str,
        context: Dict[str, Any],
        recommendations: List[Dict[str, Any]]
    ) -> bool:
        """设置推荐结果缓存（L1）"""
        key = self._get_recommendation_cache_key(scenario_id, user_id, context)
        ttl = self.cache_config["L1"]["ttl"]
        
        try:
            await self.redis.setex(
                key,
                ttl,
                json.dumps(recommendations)
            )
            return True
        except Exception as e:
            print(f"[L1 Cache] 写入失败: {e}")
            return False
    
    # ==================== L2: 热数据缓存 ====================
    
    async def get_hot_items(
        self,
        scenario_id: str,
        limit: int = 100
    ) -> Optional[List[str]]:
        """获取热门物品列表（L2）"""
        key = f"hot:items:{scenario_id}"
        
        try:
            # 从ZSET获取topN
            items = await self.redis.zrevrange(key, 0, limit - 1)
            if items:
                self.stats["L2_hits"] += 1
                return [item.decode() if isinstance(item, bytes) else item for item in items]
            else:
                self.stats["L2_misses"] += 1
                return None
        except Exception as e:
            print(f"[L2 Cache] 读取热门物品失败: {e}")
            return None
    
    async def update_hot_items(
        self,
        scenario_id: str,
        item_scores: Dict[str, float]
    ) -> bool:
        """更新热门物品列表（L2）"""
        key = f"hot:items:{scenario_id}"
        ttl = self.cache_config["L2"]["ttl"]
        
        try:
            # 使用ZSET存储，score为热度分
            pipeline = self.redis.pipeline()
            for item_id, score in item_scores.items():
                pipeline.zadd(key, {item_id: score})
            pipeline.expire(key, ttl)
            await pipeline.execute()
            return True
        except Exception as e:
            print(f"[L2 Cache] 更新热门物品失败: {e}")
            return False
    
    async def get_user_profile_cache(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取用户画像缓存（L2）"""
        key = f"hot:user:profile:{user_id}"
        
        try:
            cached = await self.redis.get(key)
            if cached:
                self.stats["L2_hits"] += 1
                return json.loads(cached)
            else:
                self.stats["L2_misses"] += 1
                return None
        except Exception as e:
            print(f"[L2 Cache] 读取用户画像失败: {e}")
            return None
    
    async def set_user_profile_cache(
        self,
        user_id: str,
        profile: Dict[str, Any]
    ) -> bool:
        """设置用户画像缓存（L2）"""
        key = f"hot:user:profile:{user_id}"
        ttl = self.cache_config["L2"]["ttl"]
        
        try:
            await self.redis.setex(
                key,
                ttl,
                json.dumps(profile)
            )
            return True
        except Exception as e:
            print(f"[L2 Cache] 写入用户画像失败: {e}")
            return False
    
    # ==================== L3: 物品详情缓存 ====================
    
    async def get_item_cache(
        self,
        item_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取单个物品详情缓存（L3）"""
        key = f"item:{item_id}"
        
        try:
            cached = await self.redis.get(key)
            if cached:
                self.stats["L3_hits"] += 1
                return json.loads(cached)
            else:
                self.stats["L3_misses"] += 1
                return None
        except Exception as e:
            print(f"[L3 Cache] 读取物品详情失败: {e}")
            return None
    
    async def get_items_cache_batch(
        self,
        item_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """批量获取物品详情缓存（L3）"""
        if not item_ids:
            return {}
        
        keys = [f"item:{item_id}" for item_id in item_ids]
        
        try:
            # 使用MGET批量获取
            values = await self.redis.mget(keys)
            
            result = {}
            for item_id, value in zip(item_ids, values):
                if value:
                    self.stats["L3_hits"] += 1
                    result[item_id] = json.loads(value)
                else:
                    self.stats["L3_misses"] += 1
            
            return result
        except Exception as e:
            print(f"[L3 Cache] 批量读取物品详情失败: {e}")
            return {}
    
    async def set_item_cache(
        self,
        item_id: str,
        item_data: Dict[str, Any]
    ) -> bool:
        """设置单个物品详情缓存（L3）"""
        key = f"item:{item_id}"
        ttl = self.cache_config["L3"]["ttl"]
        
        try:
            await self.redis.setex(
                key,
                ttl,
                json.dumps(item_data)
            )
            return True
        except Exception as e:
            print(f"[L3 Cache] 写入物品详情失败: {e}")
            return False
    
    async def set_items_cache_batch(
        self,
        items: Dict[str, Dict[str, Any]]
    ) -> bool:
        """批量设置物品详情缓存（L3）"""
        if not items:
            return True
        
        ttl = self.cache_config["L3"]["ttl"]
        
        try:
            pipeline = self.redis.pipeline()
            for item_id, item_data in items.items():
                key = f"item:{item_id}"
                pipeline.setex(key, ttl, json.dumps(item_data))
            await pipeline.execute()
            return True
        except Exception as e:
            print(f"[L3 Cache] 批量写入物品详情失败: {e}")
            return False
    
    # ==================== 缓存失效 ====================
    
    async def invalidate_item(self, item_id: str) -> bool:
        """使物品缓存失效"""
        key = f"item:{item_id}"
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"[Cache Invalidate] 失效物品缓存失败: {e}")
            return False
    
    async def invalidate_user_recommendations(
        self,
        scenario_id: str,
        user_id: str
    ) -> bool:
        """使用户推荐结果缓存失效"""
        pattern = f"rec:{scenario_id}:{user_id}:*"
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            return True
        except Exception as e:
            print(f"[Cache Invalidate] 失效用户推荐缓存失败: {e}")
            return False
    
    # ==================== 统计信息 ====================
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        l1_total = self.stats["L1_hits"] + self.stats["L1_misses"]
        l2_total = self.stats["L2_hits"] + self.stats["L2_misses"]
        l3_total = self.stats["L3_hits"] + self.stats["L3_misses"]
        
        return {
            "L1": {
                "hits": self.stats["L1_hits"],
                "misses": self.stats["L1_misses"],
                "hit_rate": self.stats["L1_hits"] / l1_total if l1_total > 0 else 0,
                "description": self.cache_config["L1"]["description"]
            },
            "L2": {
                "hits": self.stats["L2_hits"],
                "misses": self.stats["L2_misses"],
                "hit_rate": self.stats["L2_hits"] / l2_total if l2_total > 0 else 0,
                "description": self.cache_config["L2"]["description"]
            },
            "L3": {
                "hits": self.stats["L3_hits"],
                "misses": self.stats["L3_misses"],
                "hit_rate": self.stats["L3_hits"] / l3_total if l3_total > 0 else 0,
                "description": self.cache_config["L3"]["description"]
            },
            "overall_hit_rate": (
                self.stats["L1_hits"] + self.stats["L2_hits"] + self.stats["L3_hits"]
            ) / (l1_total + l2_total + l3_total) if (l1_total + l2_total + l3_total) > 0 else 0
        }
    
    def reset_stats(self):
        """重置统计信息"""
        for key in self.stats:
            self.stats[key] = 0

