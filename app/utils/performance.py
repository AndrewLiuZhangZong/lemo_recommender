"""
性能优化工具
"""
import time
import asyncio
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor
from functools import wraps


class BatchProcessor:
    """批处理器"""
    
    def __init__(self, batch_size: int = 100, max_wait_time: float = 0.1):
        """
        Args:
            batch_size: 批处理大小
            max_wait_time: 最大等待时间（秒）
        """
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.buffer = []
        self.last_flush = time.time()
    
    async def add(self, item: Any):
        """添加项到缓冲区"""
        self.buffer.append(item)
        
        # 检查是否需要flush
        if len(self.buffer) >= self.batch_size or \
           time.time() - self.last_flush >= self.max_wait_time:
            await self.flush()
    
    async def flush(self):
        """刷新缓冲区"""
        if not self.buffer:
            return
        
        items = self.buffer.copy()
        self.buffer.clear()
        self.last_flush = time.time()
        
        # 处理批量数据
        await self.process_batch(items)
    
    async def process_batch(self, items: List[Any]):
        """处理批量数据（需子类实现）"""
        raise NotImplementedError


class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    def build_index_hint(collection_name: str) -> Dict[str, Any]:
        """
        构建索引提示
        
        MongoDB索引优化建议
        """
        index_hints = {
            "items": {
                "tenant_scenario": {"tenant_id": 1, "scenario_id": 1},
                "tenant_item": {"tenant_id": 1, "item_id": 1}
            },
            "interactions": {
                "tenant_user_time": {"tenant_id": 1, "user_id": 1, "timestamp": -1},
                "tenant_scenario_time": {"tenant_id": 1, "scenario_id": 1, "timestamp": -1}
            },
            "user_profiles": {
                "tenant_user_scenario": {"tenant_id": 1, "user_id": 1, "scenario_id": 1}
            }
        }
        
        return index_hints.get(collection_name, {})
    
    @staticmethod
    def optimize_aggregation_pipeline(pipeline: List[Dict]) -> List[Dict]:
        """
        优化聚合管道
        
        优化策略:
        1. $match尽早执行
        2. $project减少字段
        3. $limit限制数据量
        """
        optimized = []
        match_stages = []
        other_stages = []
        
        # 分离$match阶段
        for stage in pipeline:
            if "$match" in stage:
                match_stages.append(stage)
            else:
                other_stages.append(stage)
        
        # $match放在最前面
        optimized.extend(match_stages)
        optimized.extend(other_stages)
        
        return optimized


class ConnectionPool:
    """连接池管理"""
    
    def __init__(self, min_size: int = 5, max_size: int = 20):
        self.min_size = min_size
        self.max_size = max_size
        self.pool = []
        self.in_use = set()
    
    async def acquire(self):
        """获取连接"""
        if self.pool:
            conn = self.pool.pop()
            self.in_use.add(conn)
            return conn
        
        if len(self.in_use) < self.max_size:
            conn = await self._create_connection()
            self.in_use.add(conn)
            return conn
        
        # 等待可用连接
        while not self.pool:
            await asyncio.sleep(0.01)
        
        return await self.acquire()
    
    async def release(self, conn):
        """释放连接"""
        if conn in self.in_use:
            self.in_use.remove(conn)
            self.pool.append(conn)
    
    async def _create_connection(self):
        """创建新连接"""
        # TODO: 实际连接创建
        return object()


def async_parallel(tasks: List[Callable], max_workers: int = 10):
    """
    并行执行异步任务
    
    使用示例:
    ```python
    results = await async_parallel([
        lambda: fetch_user_profile(user_id),
        lambda: fetch_user_items(user_id),
        lambda: fetch_user_stats(user_id)
    ])
    ```
    """
    async def run():
        return await asyncio.gather(*[task() for task in tasks])
    
    return run()


def cache_aside(
    cache_manager,
    key_prefix: str,
    ttl: int = 3600
):
    """
    Cache-Aside模式装饰器
    
    读穿透策略
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成cache key
            cache_key = cache_manager.generate_cache_key(key_prefix, *args, **kwargs)
            
            # 1. 尝试从缓存读取
            cached = await cache_manager.get(cache_key)
            if cached is not None:
                return cached
            
            # 2. 缓存未命中，查询数据库
            result = await func(*args, **kwargs)
            
            # 3. 写入缓存
            if result is not None:
                await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


class LazyLoader:
    """懒加载"""
    
    def __init__(self, loader: Callable):
        self.loader = loader
        self._value = None
        self._loaded = False
    
    async def get(self):
        """获取值（首次访问时加载）"""
        if not self._loaded:
            self._value = await self.loader()
            self._loaded = True
        return self._value


def memoize(maxsize: int = 128):
    """
    内存缓存装饰器（LRU）
    
    用于频繁调用的纯函数
    """
    from functools import lru_cache
    
    def decorator(func):
        # 对于异步函数，需要特殊处理
        if asyncio.iscoroutinefunction(func):
            cache = {}
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                key = str(args) + str(kwargs)
                
                if key in cache:
                    return cache[key]
                
                result = await func(*args, **kwargs)
                
                if len(cache) >= maxsize:
                    # 简单的FIFO清理
                    cache.pop(next(iter(cache)))
                
                cache[key] = result
                return result
            
            return wrapper
        else:
            return lru_cache(maxsize=maxsize)(func)
    
    return decorator


class PerformanceMonitor:
    """性能监控"""
    
    @staticmethod
    def track_execution_time(name: str):
        """跟踪执行时间"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start
                    if duration > 1.0:  # 超过1秒记录慢查询
                        print(f"[SlowQuery] {name} 耗时 {duration:.2f}s")
            
            return wrapper
        return decorator

