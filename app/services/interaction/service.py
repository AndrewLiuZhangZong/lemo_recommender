"""
用户行为采集服务
"""
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
import json

from app.models.interaction import (
    Interaction,
    InteractionCreate,
    ActionType
)


class InteractionService:
    """用户行为采集服务"""
    
    def __init__(self, db: AsyncIOMotorDatabase, kafka_producer=None):
        self.db = db
        self.collection = db.interactions
        self.kafka_producer = kafka_producer
    
    async def record_interaction(
        self,
        tenant_id: str,
        data: InteractionCreate
    ) -> Interaction:
        """记录单个用户行为"""
        
        # 准备行为数据
        interaction_dict = {
            "tenant_id": tenant_id,
            **data.model_dump(),
            "timestamp": data.timestamp or datetime.utcnow()
        }
        
        # 写入MongoDB
        result = await self.collection.insert_one(interaction_dict)
        interaction_dict["_id"] = result.inserted_id
        
        interaction = Interaction(**interaction_dict)
        
        # 异步发送到Kafka（实时计算）
        if self.kafka_producer:
            await self._send_to_kafka(tenant_id, interaction)
        
        return interaction
    
    async def batch_record_interactions(
        self,
        tenant_id: str,
        interactions: List[InteractionCreate]
    ) -> int:
        """批量记录用户行为"""
        
        if not interactions:
            return 0
        
        # 准备批量插入数据
        documents = []
        for data in interactions:
            doc = {
                "tenant_id": tenant_id,
                **data.model_dump(),
                "timestamp": data.timestamp or datetime.utcnow()
            }
            documents.append(doc)
        
        # 批量写入MongoDB
        result = await self.collection.insert_many(documents)
        
        # 批量发送到Kafka
        if self.kafka_producer:
            for doc in documents:
                await self._send_to_kafka(tenant_id, Interaction(**doc))
        
        return len(result.inserted_ids)
    
    async def get_user_interactions(
        self,
        tenant_id: str,
        user_id: str,
        scenario_id: Optional[str] = None,
        action_types: Optional[List[ActionType]] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[Interaction]:
        """获取用户最近的行为记录"""
        
        # 构建查询条件
        query = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=hours)}
        }
        
        if scenario_id:
            query["scenario_id"] = scenario_id
        
        if action_types:
            query["action_type"] = {"$in": action_types}
        
        # 查询
        cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
        
        interactions = []
        async for doc in cursor:
            interactions.append(Interaction(**doc))
        
        return interactions
    
    async def get_item_interactions(
        self,
        tenant_id: str,
        item_id: str,
        scenario_id: str,
        action_types: Optional[List[ActionType]] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[Interaction]:
        """获取物品最近的行为记录"""
        
        # 构建查询条件
        query = {
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "item_id": item_id,
            "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=hours)}
        }
        
        if action_types:
            query["action_type"] = {"$in": action_types}
        
        # 查询
        cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
        
        interactions = []
        async for doc in cursor:
            interactions.append(Interaction(**doc))
        
        return interactions
    
    async def get_interaction_stats(
        self,
        tenant_id: str,
        scenario_id: str,
        hours: int = 24
    ) -> dict:
        """获取行为统计"""
        
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 使用聚合查询统计
        pipeline = [
            {
                "$match": {
                    "tenant_id": tenant_id,
                    "scenario_id": scenario_id,
                    "timestamp": {"$gte": since_time}
                }
            },
            {
                "$group": {
                    "_id": "$action_type",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        stats = {}
        async for doc in self.collection.aggregate(pipeline):
            stats[doc["_id"]] = doc["count"]
        
        return {
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "time_range_hours": hours,
            "stats": stats,
            "total": sum(stats.values())
        }
    
    async def _send_to_kafka(self, tenant_id: str, interaction: Interaction):
        """发送行为数据到Kafka"""
        
        try:
            # Kafka Topic: user-behaviors-{tenant_id}
            topic = f"user-behaviors-{tenant_id}"
            
            # 准备消息
            message = {
                "tenant_id": interaction.tenant_id,
                "scenario_id": interaction.scenario_id,
                "user_id": interaction.user_id,
                "item_id": interaction.item_id,
                "action_type": interaction.action_type.value,
                "context": interaction.context,
                "extra": interaction.extra,
                "timestamp": interaction.timestamp.isoformat()
            }
            
            # 发送（异步）
            # await self.kafka_producer.send(topic, value=message)
            
            # TODO: 实际Kafka集成
            pass
        except Exception as e:
            # 记录错误但不影响主流程
            print(f"Kafka发送失败: {e}")

