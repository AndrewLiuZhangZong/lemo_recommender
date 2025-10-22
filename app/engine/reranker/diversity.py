"""
多样性重排策略
"""
from typing import List, Tuple, Set
from app.engine.reranker.base import Reranker


class DiversityReranker(Reranker):
    """多样性重排器"""
    
    def __init__(self, db=None, window_size: int = 5):
        super().__init__("diversity")
        self.db = db
        self.window_size = window_size  # 滑动窗口大小
    
    async def rerank(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        ranked_items: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        """基于多样性重排"""
        
        if not ranked_items or len(ranked_items) <= self.window_size:
            return ranked_items
        
        try:
            # 获取物品的分类信息
            item_ids = [item_id for item_id, _ in ranked_items]
            items_collection = self.db.items
            items = await items_collection.find({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "item_id": {"$in": item_ids}
            }).to_list(length=len(item_ids))
            
            # 构建item_id -> category映射
            item_category_map = {}
            for item in items:
                item_id = item["item_id"]
                category = item.get("metadata", {}).get("category", "unknown")
                item_category_map[item_id] = category
            
            # 滑动窗口多样性重排
            result = []
            remaining = list(ranked_items)
            
            while remaining:
                # 取第一个
                if not result:
                    result.append(remaining.pop(0))
                    continue
                
                # 获取窗口内已选择的分类
                window_categories: Set[str] = set()
                for item_id, _ in result[-self.window_size:]:
                    cat = item_category_map.get(item_id, "unknown")
                    window_categories.add(cat)
                
                # 优先选择不同分类的物品
                selected_idx = 0
                for idx, (item_id, score) in enumerate(remaining):
                    cat = item_category_map.get(item_id, "unknown")
                    if cat not in window_categories:
                        selected_idx = idx
                        break
                
                result.append(remaining.pop(selected_idx))
            
            return result
            
        except Exception as e:
            print(f"多样性重排失败: {e}")
            return ranked_items


class FreshnessReranker(Reranker):
    """新鲜度重排器"""
    
    def __init__(self, db=None, boost_factor: float = 0.2):
        super().__init__("freshness")
        self.db = db
        self.boost_factor = boost_factor
    
    async def rerank(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        ranked_items: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        """基于新鲜度重排"""
        
        if not ranked_items:
            return ranked_items
        
        try:
            from datetime import datetime, timedelta
            
            # 获取物品发布时间
            item_ids = [item_id for item_id, _ in ranked_items]
            items_collection = self.db.items
            items = await items_collection.find({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "item_id": {"$in": item_ids}
            }).to_list(length=len(item_ids))
            
            # 构建item_id -> freshness_score映射
            now = datetime.utcnow()
            item_freshness_map = {}
            
            for item in items:
                item_id = item["item_id"]
                publish_time = item.get("metadata", {}).get("publish_time")
                
                if publish_time:
                    if isinstance(publish_time, str):
                        publish_time = datetime.fromisoformat(publish_time.replace("Z", "+00:00"))
                    
                    # 计算时间衰减
                    age_days = (now - publish_time).days
                    if age_days < 1:
                        freshness_score = 1.0
                    elif age_days < 7:
                        freshness_score = 0.8
                    elif age_days < 30:
                        freshness_score = 0.5
                    else:
                        freshness_score = 0.2
                else:
                    freshness_score = 0.5  # 默认值
                
                item_freshness_map[item_id] = freshness_score
            
            # 调整分数
            reranked_items = []
            for item_id, score in ranked_items:
                freshness = item_freshness_map.get(item_id, 0.5)
                new_score = score * (1 + self.boost_factor * freshness)
                reranked_items.append((item_id, new_score))
            
            # 重新排序
            reranked_items.sort(key=lambda x: x[1], reverse=True)
            
            return reranked_items
            
        except Exception as e:
            print(f"新鲜度重排失败: {e}")
            return ranked_items

