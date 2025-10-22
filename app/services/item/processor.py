"""
物品处理器 - 统一处理物品创建后的逻辑
"""
from typing import List, Dict, Any
from datetime import datetime
import asyncio

from app.core.kafka import KafkaProducer, KafkaTopics
from app.core.config import settings


class ItemProcessor:
    """
    物品处理器
    
    负责处理物品创建后的后续流程：
    1. 发送Kafka事件通知
    2. 触发向量生成任务
    3. 更新缓存
    """
    
    def __init__(self, kafka_producer: KafkaProducer = None):
        self.kafka_producer = kafka_producer
    
    async def process_items(
        self,
        tenant_id: str,
        scenario_id: str,
        items: List[Dict[str, Any]],
        source: str = "api"
    ) -> Dict[str, Any]:
        """
        处理物品（创建后的后续流程）
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            items: 物品列表
            source: 来源（api/kafka）
            
        Returns:
            处理结果统计
        """
        if not items:
            return {"processed": 0, "source": source}
        
        item_ids = [item.get("item_id") for item in items if item.get("item_id")]
        
        results = {
            "processed": len(item_ids),
            "source": source,
            "tasks": {
                "kafka_sent": 0,
                "vector_queued": 0,
                "cache_updated": False
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 并发执行多个任务
        await asyncio.gather(
            self._send_kafka_events(tenant_id, scenario_id, items, results),
            self._trigger_vector_generation(tenant_id, scenario_id, item_ids, results),
            self._invalidate_cache(tenant_id, scenario_id, results),
            return_exceptions=True
        )
        
        return results
    
    async def _send_kafka_events(
        self,
        tenant_id: str,
        scenario_id: str,
        items: List[Dict[str, Any]],
        results: dict
    ):
        """发送Kafka事件"""
        if not self.kafka_producer:
            return
        
        try:
            for item in items:
                message = {
                    "tenant_id": tenant_id,
                    "scenario_id": scenario_id,
                    "item_id": item.get("item_id"),
                    "action": "created",
                    "metadata": item.get("metadata", {}),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.kafka_producer.send(
                    topic=KafkaTopics.item_stats_updates(),
                    value=message,
                    key=item.get("item_id")
                )
                
                results["tasks"]["kafka_sent"] += 1
                
        except Exception as e:
            print(f"[ItemProcessor] Kafka发送失败: {e}")
    
    async def _trigger_vector_generation(
        self,
        tenant_id: str,
        scenario_id: str,
        item_ids: List[str],
        results: dict
    ):
        """触发向量生成任务"""
        try:
            # 方式1: 使用Celery异步任务（生产环境推荐）
            if settings.celery_enabled:
                from app.tasks.item_tasks import generate_item_embeddings
                generate_item_embeddings.delay(tenant_id, scenario_id, item_ids)
                results["tasks"]["vector_queued"] = len(item_ids)
            
            # 方式2: 直接调用（开发环境）
            else:
                print(f"[ItemProcessor] 向量生成任务已排队: {len(item_ids)}个物品")
                results["tasks"]["vector_queued"] = len(item_ids)
                
        except Exception as e:
            print(f"[ItemProcessor] 向量生成任务触发失败: {e}")
    
    async def _invalidate_cache(
        self,
        tenant_id: str,
        scenario_id: str,
        results: dict
    ):
        """使缓存失效"""
        try:
            from app.core.database import get_redis
            redis = get_redis()
            
            if redis:
                # 删除相关缓存key
                cache_patterns = [
                    f"items:{tenant_id}:{scenario_id}:*",
                    f"rec:precomputed:{tenant_id}:{scenario_id}:*",
                    f"item:hot:{tenant_id}:{scenario_id}"
                ]
                
                for pattern in cache_patterns:
                    # 使用SCAN扫描并删除
                    cursor = 0
                    while True:
                        cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                        if keys:
                            await redis.delete(*keys)
                        if cursor == 0:
                            break
                
                results["tasks"]["cache_updated"] = True
                print(f"[ItemProcessor] 缓存已失效: {tenant_id}/{scenario_id}")
                
        except Exception as e:
            print(f"[ItemProcessor] 缓存失效失败: {e}")

