# -*- coding: utf-8 -*-
"""
实时推荐流服务
职责：实时推荐结果计算、Kafka流处理、实时召回触发
"""
import sys
import os
import asyncio
import json
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.service_config import ServiceConfig


class RealtimeStreamService:
    """实时推荐流服务"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.kafka_servers = config.kafka_bootstrap_servers
        self.consumer = None
        self.producer = None
        print("[RealtimeStreamService] 初始化完成")
    
    async def start(self):
        """启动Kafka消费者和生产者"""
        # 创建消费者（消费用户行为事件）
        self.consumer = AIOKafkaConsumer(
            'user_behaviors',
            bootstrap_servers=self.kafka_servers,
            group_id='realtime-stream-service',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        # 创建生产者（发送实时推荐结果）
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        await self.consumer.start()
        await self.producer.start()
        
        print("[RealtimeStreamService] Kafka连接已建立")
    
    async def process_events(self):
        """处理用户行为事件"""
        try:
            async for message in self.consumer:
                event = message.value
                
                # 解析事件
                user_id = event.get('user_id')
                action_type = event.get('action_type')
                tenant_id = event.get('tenant_id')
                scenario_id = event.get('scenario_id')
                
                # 实时推荐触发逻辑（简化版）
                if action_type in ['VIEW', 'LIKE', 'FAVORITE']:
                    # 触发实时召回
                    recommendation = {
                        "user_id": user_id,
                        "tenant_id": tenant_id,
                        "scenario_id": scenario_id,
                        "trigger_type": action_type,
                        "timestamp": event.get('timestamp')
                    }
                    
                    # 发送到实时推荐topic
                    await self.producer.send_and_wait(
                        'realtime_recommendations',
                        recommendation
                    )
                    
                    print(f"[RealtimeStreamService] 触发实时推荐: {user_id}")
        except Exception as e:
            print(f"[RealtimeStreamService] 处理事件失败: {e}")
    
    async def stop(self):
        """停止服务"""
        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()


async def main():
    """主函数"""
    config = ServiceConfig()
    service = RealtimeStreamService(config)
    
    try:
        await service.start()
        print("[RealtimeStreamService] 服务已启动，开始处理事件...")
        await service.process_events()
    except KeyboardInterrupt:
        print("[RealtimeStreamService] 收到停止信号")
    finally:
        await service.stop()
        print("[RealtimeStreamService] 服务已停止")


if __name__ == '__main__':
    asyncio.run(main())

