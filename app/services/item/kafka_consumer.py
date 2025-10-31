"""
物品Kafka消费者服务
"""
import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime

from app.core.kafka import KafkaConsumer, KafkaProducer, KafkaTopics
from app.core.config import settings
from app.core.database import get_database
from app.services.item.service import ItemService
from app.services.item.processor import ItemProcessor


class ItemKafkaConsumerService:
    """
    物品Kafka消费者服务
    
    监听业务系统的Kafka消息，自动接入物品数据
    """
    
    def __init__(self):
        # 消费Topic：业务系统推送物品数据
        # 可通过环境变量配置：KAFKA_ITEM_INGEST_TOPICS
        self.topics = settings.kafka_item_ingest_topics
        
        self.consumer = None
        self.producer = None
        self.db = None
        self.processor = None
        self.running = False
        
        print(f"[ItemKafkaConsumer] 初始化，监听Topics: {self.topics}")
    
    async def ensure_topics_exist(self):
        """确保所需的 Kafka Topics 存在，不存在则自动创建"""
        try:
            from aiokafka import AIOKafkaClient
            from aiokafka.admin import AIOKafkaAdminClient, NewTopic
            from aiokafka.errors import TopicAlreadyExistsError, KafkaError
            
            print(f"[ItemKafkaConsumer] 🔍 检查 Kafka Topics...")
            
            # 创建 Admin Client
            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                client_id='kafka-topic-checker'
            )
            
            try:
                await admin_client.start()
                
                # 获取现有 Topics
                client = AIOKafkaClient(bootstrap_servers=settings.kafka_bootstrap_servers)
                await client.bootstrap()
                cluster = client.cluster
                existing_topics = cluster.topics()
                await client.close()
                
                # 检查哪些 Topics 需要创建
                topics_to_create = []
                for topic_name in self.topics:
                    if topic_name not in existing_topics:
                        topics_to_create.append(
                            NewTopic(
                                name=topic_name,
                                num_partitions=3,
                                replication_factor=1
                            )
                        )
                        print(f"[ItemKafkaConsumer] 📝 Topic 不存在，准备创建: {topic_name}")
                    else:
                        print(f"[ItemKafkaConsumer] ✓ Topic 已存在: {topic_name}")
                
                # 创建缺失的 Topics
                if topics_to_create:
                    print(f"[ItemKafkaConsumer] 🚀 创建 {len(topics_to_create)} 个 Topics...")
                    try:
                        await admin_client.create_topics(topics_to_create, timeout_ms=10000)
                        for topic in topics_to_create:
                            print(f"[ItemKafkaConsumer] ✅ Topic 创建成功: {topic.name}")
                    except TopicAlreadyExistsError:
                        print(f"[ItemKafkaConsumer] ⚠️  某些 Topic 已存在（并发创建）")
                    except Exception as e:
                        print(f"[ItemKafkaConsumer] ⚠️  Topic 创建失败: {e}")
                        print(f"[ItemKafkaConsumer] 将尝试继续启动（Topic 可能已存在或权限不足）")
                else:
                    print(f"[ItemKafkaConsumer] ✅ 所有 Topics 已就绪")
                
            finally:
                await admin_client.close()
                
        except ImportError:
            print(f"[ItemKafkaConsumer] ⚠️  aiokafka.admin 不可用，跳过 Topic 检查")
        except Exception as e:
            print(f"[ItemKafkaConsumer] ⚠️  Topic 检查失败: {e}")
            print(f"[ItemKafkaConsumer] 将尝试继续启动...")
    
    async def start(self):
        """启动消费者服务"""
        try:
            # 1. 确保 Topics 存在
            await self.ensure_topics_exist()
            
            # 2. 初始化Kafka消费者
            self.consumer = KafkaConsumer(
                topics=self.topics,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=settings.kafka_consumer_group
            )
            await self.consumer.start()
            
            # 初始化Kafka生产者（用于发送处理结果）
            self.producer = KafkaProducer(settings.kafka_bootstrap_servers)
            await self.producer.start()
            
            # 初始化MongoDB（同步版本用于 Consumer）
            self.db = get_database()
            
            # 初始化处理器
            self.processor = ItemProcessor(self.producer)
            
            self.running = True
            
            print("[ItemKafkaConsumer] ✅ 服务已启动")
            
            # 开始消费消息
            await self._consume_loop()
            
        except Exception as e:
            print(f"[ItemKafkaConsumer] ❌ 启动失败: {e}")
            await self.stop()
    
    async def stop(self):
        """停止消费者服务"""
        self.running = False
        
        if self.consumer:
            await self.consumer.stop()
        
        if self.producer:
            await self.producer.stop()
        
        print("[ItemKafkaConsumer] 服务已停止")
    
    async def _consume_loop(self):
        """消费循环"""
        print("[ItemKafkaConsumer] 开始消费消息...")
        
        try:
            async for message in self.consumer.consume():
                if not self.running:
                    break
                
                await self._process_message(message)
                
        except Exception as e:
            print(f"[ItemKafkaConsumer] 消费循环异常: {e}")
    
    async def _process_message(self, message: Dict[str, Any]):
        """
        处理单条Kafka消息
        
        消息格式示例:
        {
            "tenant_id": "vlog_platform",
            "scenario_id": "vlog_main_feed",
            "items": [
                {
                    "item_id": "vlog_001",
                    "metadata": {
                        "title": "北京旅行Vlog",
                        "author": "旅行博主",
                        "duration": 180,
                        "tags": ["旅行", "北京"]
                    }
                }
            ]
        }
        """
        try:
            topic = message.get('topic')
            value = message.get('value')
            
            if not value:
                return
            
            # 提取必要字段
            tenant_id = value.get('tenant_id')
            scenario_id = value.get('scenario_id')
            items = value.get('items', [])
            
            if not tenant_id or not scenario_id or not items:
                print(f"[ItemKafkaConsumer] ⚠️ 消息格式不完整: {value}")
                return
            
            print(f"[ItemKafkaConsumer] 收到消息: Topic={topic}, "
                  f"Tenant={tenant_id}, Scenario={scenario_id}, "
                  f"Items={len(items)}")
            
            # 1. 写入MongoDB
            service = ItemService(self.db)
            count = await service.batch_create_items(
                tenant_id=tenant_id,
                scenario_id=scenario_id,
                items=items
            )
            
            print(f"[ItemKafkaConsumer] ✅ 写入MongoDB: {count}个物品")
            
            # 2. 触发后续处理
            process_result = await self.processor.process_items(
                tenant_id=tenant_id,
                scenario_id=scenario_id,
                items=items,
                source="kafka"
            )
            
            print(f"[ItemKafkaConsumer] ✅ 处理完成: {process_result}")
            
            # 3. 发送处理结果（可选：回调业务系统）
            await self._send_result(tenant_id, scenario_id, count, process_result)
            
        except Exception as e:
            print(f"[ItemKafkaConsumer] ❌ 处理消息失败: {e}")
            # 可以实现死信队列或重试机制
    
    async def _send_result(
        self,
        tenant_id: str,
        scenario_id: str,
        count: int,
        process_result: Dict[str, Any]
    ):
        """发送处理结果（可选）"""
        try:
            result_message = {
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "count": count,
                "process_result": process_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 发送到结果Topic（业务系统可订阅）
            await self.producer.send(
                topic="items-ingest-results",
                value=result_message,
                key=tenant_id
            )
            
        except Exception as e:
            print(f"[ItemKafkaConsumer] 发送结果失败: {e}")


async def run_item_kafka_consumer():
    """
    运行物品Kafka消费者（守护进程入口）
    """
    consumer_service = ItemKafkaConsumerService()
    
    try:
        await consumer_service.start()
    except KeyboardInterrupt:
        print("\n[ItemKafkaConsumer] 收到中断信号")
    finally:
        await consumer_service.stop()


if __name__ == "__main__":
    # 可以直接运行此脚本启动消费者
    print("=" * 50)
    print("物品Kafka消费者服务")
    print("=" * 50)
    
    asyncio.run(run_item_kafka_consumer())

