"""
缓存管理器 - 优化缓存策略
"""
from typing import Any, Optional, Callable
import json
import hashlib
from functools import wraps
from app.core.redis_client import get_redis_client


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis_client()
        self.default_ttl = 3600  # 1小时
    
    def generate_cache_key(
        self,
        prefix: str,
        *args,
        **kwargs
    ) -> str:
        """
        生成缓存key
        
        Args:
            prefix: 前缀
            args: 位置参数
            kwargs: 关键字参数
        
        Returns:
            缓存key
        """
        # 将参数序列化并生成哈希
        params_str = json.dumps({
            "args": args,
            "kwargs": sorted(kwargs.items())
        }, sort_keys=True)
        
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:16]
        
        return f"{prefix}:{params_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"[Cache] 获取失败: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """设置缓存"""
        try:
            ttl = ttl or self.default_ttl
            self.redis.setex(
                key,
                ttl,
                json.dumps(value, ensure_ascii=False, default=str)
            )
        except Exception as e:
            print(f"[Cache] 设置失败: {e}")
    
    async def delete(self, key: str):
        """删除缓存"""
        try:
            self.redis.delete(key)
        except Exception as e:
            print(f"[Cache] 删除失败: {e}")
    
    async def delete_pattern(self, pattern: str):
        """删除匹配模式的所有key"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        except Exception as e:
            print(f"[Cache] 批量删除失败: {e}")
    
    def cache_result(
        self,
        prefix: str,
        ttl: Optional[int] = None,
        key_builder: Optional[Callable] = None
    ):
        """
        缓存装饰器
        
        Args:
            prefix: 缓存key前缀
            ttl: 过期时间（秒）
            key_builder: 自定义key生成函数
        
        使用示例:
        ```python
        @cache_manager.cache_result("user:profile", ttl=3600)
        async def get_user_profile(user_id: str):
            return {"user_id": user_id, "name": "xxx"}
        ```
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存key
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = self.generate_cache_key(prefix, *args, **kwargs)
                
                # 尝试从缓存获取
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    print(f"[Cache] 命中: {cache_key}")
                    return cached_value
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 写入缓存
                if result is not None:
                    await self.set(cache_key, result, ttl)
                    print(f"[Cache] 写入: {cache_key}")
                
                return result
            
            return wrapper
        return decorator
    
    async def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        try:
            info = self.redis.info("stats")
            memory = self.redis.info("memory")
            
            return {
                "total_keys": self.redis.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                ),
                "memory_used": memory.get("used_memory_human", "N/A"),
                "memory_peak": memory.get("used_memory_peak_human", "N/A")
            }
        except Exception as e:
            print(f"[Cache] 获取统计失败: {e}")
            return {}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """计算缓存命中率"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round(hits / total, 4)
    
    async def warm_up(
        self,
        tenant_id: str,
        scenario_id: str,
        db
    ):
        """
        缓存预热
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            db: 数据库连接
        """
        print(f"[Cache] 开始预热: {tenant_id}/{scenario_id}")
        
        # 1. 预热场景配置
        scenario = await db.scenarios.find_one({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id
        })
        if scenario:
            key = f"scenario:{tenant_id}:{scenario_id}"
            await self.set(key, scenario, ttl=86400)  # 24小时
        
        # 2. 预热热门物品
        hot_items = await db.items.find({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id
        }).sort("metadata.view_count", -1).limit(100).to_list(length=100)
        
        for item in hot_items:
            key = f"item:{tenant_id}:{item['item_id']}"
            await self.set(key, item, ttl=3600)
        
        print(f"[Cache] 预热完成: 场景1个, 物品{len(hot_items)}个")


# 全局缓存管理器实例
cache_manager = CacheManager()

