"""
协同过滤召回策略
"""
from typing import List, Dict, Any
from app.engine.recall.base import RecallStrategy


class CollaborativeFilteringRecall(RecallStrategy):
    """协同过滤召回（User-Based CF）"""
    
    def __init__(self, db=None):
        super().__init__("collaborative_filtering")
        self.db = db
    
    async def recall(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        limit: int = 100,
        params: Dict[str, Any] = None
    ) -> List[str]:
        """基于用户协同过滤召回"""
        
        if not self.db:
            return []
        
        try:
            # 1. 获取用户最近交互的物品
            interactions_collection = self.db.interactions
            recent_interactions = await interactions_collection.find({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "user_id": user_id,
                "action_type": {"$in": ["click", "view", "like"]}
            }).sort("timestamp", -1).limit(50).to_list(length=50)
            
            if not recent_interactions:
                return []
            
            interacted_item_ids = [i["item_id"] for i in recent_interactions]
            
            # 2. 找到与当前用户相似的其他用户（交互了相同物品的用户）
            similar_users = await interactions_collection.aggregate([
                {
                    "$match": {
                        "tenant_id": tenant_id,
                        "scenario_id": scenario_id,
                        "item_id": {"$in": interacted_item_ids},
                        "user_id": {"$ne": user_id}
                    }
                },
                {
                    "$group": {
                        "_id": "$user_id",
                        "common_items": {"$addToSet": "$item_id"}
                    }
                },
                {"$limit": 100}
            ]).to_list(length=100)
            
            if not similar_users:
                return []
            
            similar_user_ids = [u["_id"] for u in similar_users]
            
            # 3. 获取相似用户交互过的物品（排除当前用户已交互的）
            candidate_items = await interactions_collection.aggregate([
                {
                    "$match": {
                        "tenant_id": tenant_id,
                        "scenario_id": scenario_id,
                        "user_id": {"$in": similar_user_ids},
                        "item_id": {"$nin": interacted_item_ids},
                        "action_type": {"$in": ["click", "view", "like"]}
                    }
                },
                {
                    "$group": {
                        "_id": "$item_id",
                        "score": {"$sum": 1}  # 简单计数作为分数
                    }
                },
                {"$sort": {"score": -1}},
                {"$limit": limit}
            ]).to_list(length=limit)
            
            return [item["_id"] for item in candidate_items]
            
        except Exception as e:
            print(f"协同过滤召回失败: {e}")
            return []


class ItemBasedCFRecall(RecallStrategy):
    """基于物品的协同过滤召回"""
    
    def __init__(self, db=None):
        super().__init__("item_based_cf")
        self.db = db
    
    async def recall(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        limit: int = 100,
        params: Dict[str, Any] = None
    ) -> List[str]:
        """基于物品协同过滤召回"""
        
        if not self.db:
            return []
        
        try:
            # 1. 获取用户最近交互的物品
            interactions_collection = self.db.interactions
            recent_items = await interactions_collection.find({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "user_id": user_id,
                "action_type": {"$in": ["click", "view", "like"]}
            }).sort("timestamp", -1).limit(10).to_list(length=10)
            
            if not recent_items:
                return []
            
            seed_item_ids = [i["item_id"] for i in recent_items]
            
            # 2. 找到与这些物品相似的物品（被相同用户交互过）
            similar_items = await interactions_collection.aggregate([
                {
                    "$match": {
                        "tenant_id": tenant_id,
                        "scenario_id": scenario_id,
                        "item_id": {"$in": seed_item_ids}
                    }
                },
                {
                    "$lookup": {
                        "from": "interactions",
                        "let": {"user_id": "$user_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$and": [
                                            {"$eq": ["$user_id", "$$user_id"]},
                                            {"$eq": ["$tenant_id", tenant_id]},
                                            {"$eq": ["$scenario_id", scenario_id]},
                                            {"$not": {"$in": ["$item_id", seed_item_ids]}}
                                        ]
                                    }
                                }
                            }
                        ],
                        "as": "related_items"
                    }
                },
                {"$unwind": "$related_items"},
                {
                    "$group": {
                        "_id": "$related_items.item_id",
                        "score": {"$sum": 1}
                    }
                },
                {"$sort": {"score": -1}},
                {"$limit": limit}
            ]).to_list(length=limit)
            
            return [item["_id"] for item in similar_items]
            
        except Exception as e:
            print(f"基于物品的协同过滤召回失败: {e}")
            return []

