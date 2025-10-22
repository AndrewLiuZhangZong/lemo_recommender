"""
向量召回策略
"""
from typing import List, Dict, Any
from app.engine.recall.base import RecallStrategy
from app.core.milvus_client import MilvusClient, EmbeddingGenerator


class VectorSearchRecall(RecallStrategy):
    """基于向量相似度的召回"""
    
    def __init__(self, milvus_client: MilvusClient, db=None):
        super().__init__("vector_search")
        self.milvus = milvus_client
        self.db = db
        self.embedding_generator = EmbeddingGenerator()
    
    async def recall(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        limit: int = 100,
        params: Dict[str, Any] = None
    ) -> List[str]:
        """基于向量相似度召回"""
        
        if not self.milvus.enabled:
            print("[VectorSearch] Milvus未启用，跳过向量召回")
            return []
        
        try:
            # 1. 获取用户最近交互的物品
            interactions_collection = self.db.interactions
            recent_interactions = await interactions_collection.find({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "user_id": user_id,
                "action_type": {"$in": ["click", "view", "like"]}
            }).sort("timestamp", -1).limit(20).to_list(length=20)
            
            if not recent_interactions:
                return []
            
            # 2. 生成用户向量（基于交互历史）
            user_embedding = self.embedding_generator.generate_user_embedding(
                recent_interactions
            )
            
            # 3. 从Milvus中搜索相似物品
            # 获取场景类型
            scenarios_collection = self.db.scenarios
            scenario = await scenarios_collection.find_one({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id
            })
            
            if not scenario:
                return []
            
            scenario_type = scenario.get("scenario_type", "custom")
            collection_name = f"items_embeddings_{scenario_type}"
            
            # 4. 向量相似度搜索
            similar_items = await self.milvus.search_similar(
                collection_name=collection_name,
                tenant_id=tenant_id,
                scenario_id=scenario_id,
                query_embedding=user_embedding,
                top_k=limit * 2  # 召回2倍，后续过滤
            )
            
            # 5. 过滤已交互物品
            interacted_item_ids = {i["item_id"] for i in recent_interactions}
            item_ids = [
                item["item_id"]
                for item in similar_items
                if item["item_id"] not in interacted_item_ids
            ]
            
            return item_ids[:limit]
            
        except Exception as e:
            print(f"[VectorSearch] 向量召回失败: {e}")
            return []


class Item2ItemVectorRecall(RecallStrategy):
    """基于物品的向量召回（I2I）"""
    
    def __init__(self, milvus_client: MilvusClient, db=None):
        super().__init__("item2item_vector")
        self.milvus = milvus_client
        self.db = db
    
    async def recall(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        limit: int = 100,
        params: Dict[str, Any] = None
    ) -> List[str]:
        """基于物品的向量召回"""
        
        if not self.milvus.enabled:
            return []
        
        try:
            # 1. 获取用户最近交互的物品
            interactions_collection = self.db.interactions
            recent_items = await interactions_collection.find({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "user_id": user_id,
                "action_type": {"$in": ["view", "like"]}
            }).sort("timestamp", -1).limit(5).to_list(length=5)
            
            if not recent_items:
                return []
            
            seed_item_ids = [i["item_id"] for i in recent_items]
            
            # 2. 获取seed物品的向量
            items_collection = self.db.items
            seed_items = await items_collection.find({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "item_id": {"$in": seed_item_ids}
            }).to_list(length=len(seed_item_ids))
            
            # 3. 对每个seed物品找相似物品
            all_similar_items = []
            scenario = await self.db.scenarios.find_one({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id
            })
            
            if not scenario:
                return []
            
            scenario_type = scenario.get("scenario_type", "custom")
            collection_name = f"items_embeddings_{scenario_type}"
            
            for seed_item in seed_items:
                embedding = seed_item.get("embedding")
                if not embedding:
                    continue
                
                # 向量搜索
                similar_items = await self.milvus.search_similar(
                    collection_name=collection_name,
                    tenant_id=tenant_id,
                    scenario_id=scenario_id,
                    query_embedding=embedding,
                    top_k=limit // len(seed_items)  # 平均分配
                )
                
                all_similar_items.extend(similar_items)
            
            # 4. 去重并排序
            seen = set()
            unique_items = []
            for item in sorted(all_similar_items, key=lambda x: x["score"], reverse=True):
                item_id = item["item_id"]
                if item_id not in seen and item_id not in seed_item_ids:
                    seen.add(item_id)
                    unique_items.append(item_id)
            
            return unique_items[:limit]
            
        except Exception as e:
            print(f"[Item2ItemVector] I2I向量召回失败: {e}")
            return []

