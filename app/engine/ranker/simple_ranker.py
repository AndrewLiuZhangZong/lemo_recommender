"""
简单排序器
"""
from typing import List, Dict, Any, Tuple
import random
from app.engine.ranker.base import Ranker


class SimpleScoreRanker(Ranker):
    """简单评分排序器（基于规则）"""
    
    def __init__(self, db=None):
        super().__init__("simple_score")
        self.db = db
    
    async def rank(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        item_ids: List[str],
        features: Dict[str, Any] = None
    ) -> List[Tuple[str, float]]:
        """简单评分排序"""
        
        if not item_ids:
            return []
        
        try:
            # 获取物品信息
            items_collection = self.db.items
            items = await items_collection.find({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "item_id": {"$in": item_ids}
            }).to_list(length=len(item_ids))
            
            # 简单评分规则
            scored_items = []
            for item in items:
                score = 0.0
                metadata = item.get("metadata", {})
                
                # 基于元数据的简单评分
                if "view_count" in metadata:
                    score += metadata["view_count"] * 0.0001  # 观看数
                
                if "like_count" in metadata:
                    score += metadata["like_count"] * 0.001  # 点赞数
                
                if "completion_rate" in metadata:
                    score += metadata["completion_rate"] * 10  # 完播率
                
                # 添加随机性
                score += random.random() * 0.1
                
                scored_items.append((item["item_id"], score))
            
            # 按分数降序排序
            scored_items.sort(key=lambda x: x[1], reverse=True)
            
            return scored_items
            
        except Exception as e:
            print(f"排序失败: {e}")
            # 降级：返回随机顺序
            return [(item_id, random.random()) for item_id in item_ids]


class RandomRanker(Ranker):
    """随机排序器（兜底策略）"""
    
    def __init__(self):
        super().__init__("random")
    
    async def rank(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        item_ids: List[str],
        features: Dict[str, Any] = None
    ) -> List[Tuple[str, float]]:
        """随机排序"""
        
        scored_items = [(item_id, random.random()) for item_id in item_ids]
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return scored_items

