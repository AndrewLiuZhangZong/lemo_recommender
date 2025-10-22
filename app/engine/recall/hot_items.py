"""
热门物品召回策略
"""
from typing import List, Dict, Any
from app.engine.recall.base import RecallStrategy


class HotItemsRecall(RecallStrategy):
    """热门物品召回"""
    
    def __init__(self, redis_client=None):
        super().__init__("hot_items")
        self.redis = redis_client
    
    async def recall(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        limit: int = 100,
        params: Dict[str, Any] = None
    ) -> List[str]:
        """召回热门物品"""
        
        if not self.redis:
            return []
        
        try:
            # 从Redis ZSET获取热门物品
            # Key: hot:items:{tenant_id}:{scenario_id}
            key = f"hot:items:{tenant_id}:{scenario_id}"
            
            # 获取分数最高的N个物品（Flink实时计算的热度）
            # TODO: 实际Redis集成
            # hot_items = await self.redis.zrevrange(key, 0, limit - 1)
            
            # 临时返回空列表（等待Flink实现）
            return []
            
        except Exception as e:
            print(f"热门召回失败: {e}")
            return []

