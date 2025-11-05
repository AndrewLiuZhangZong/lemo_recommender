# -*- coding: utf-8 -*-
"""
行为服务 - gRPC实现
职责：用户行为采集、发送到Kafka、统计信息
"""
import sys
import os
import asyncio
import uuid
import time
from typing import List
from concurrent import futures

import grpc
from aiokafka import AIOKafkaProducer
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.config import settings
from app.core.service_config import ServiceConfig
from app.grpc_generated.python.recommender.v1 import behavior_pb2
from app.grpc_generated.python.recommender.v1 import behavior_pb2_grpc


class BehaviorService:
    """行为服务核心逻辑"""
    
    def __init__(self, kafka_producer: AIOKafkaProducer):
        self.kafka_producer = kafka_producer
        self.stats = {
            "total_events": 0,
            "kafka_success": 0,
            "kafka_failed": 0,
            "rejected": 0
        }
        print("[BehaviorService] 初始化完成")
    
    async def track_event(self, event: dict) -> tuple[bool, str]:
        """采集单个行为事件"""
        # 验证tenant_id（SaaS多租户隔离）
        if not event.get("tenant_id"):
            self.stats["rejected"] += 1
            return False, "Missing tenant_id"
        
        # 生成event_id和timestamp
        if not event.get("event_id"):
            event["event_id"] = str(uuid.uuid4())
        if not event.get("timestamp"):
            event["timestamp"] = int(time.time() * 1000)
        
        self.stats["total_events"] += 1
        
        # 发送到Kafka
        try:
            topic = "user_behaviors"
            message = json.dumps(event).encode('utf-8')
            await self.kafka_producer.send_and_wait(topic, message)
            self.stats["kafka_success"] += 1
            print(f"[BehaviorService] 事件发送成功: {event['event_id']}")
            return True, event["event_id"]
        except Exception as e:
            self.stats["kafka_failed"] += 1
            print(f"[BehaviorService] Kafka发送失败: {e}")
            return False, str(e)
    
    async def track_batch(self, events: List[dict]) -> tuple[int, int, List[str]]:
        """批量采集行为事件"""
        succeeded = 0
        failed = 0
        errors = []
        
        for event in events:
            success, msg = await self.track_event(event)
            if success:
                succeeded += 1
            else:
                failed += 1
                errors.append(msg)
        
        return succeeded, failed, errors
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        total = self.stats["total_events"]
        success_rate = (self.stats["kafka_success"] / total * 100) if total > 0 else 0
        return {
            **self.stats,
            "success_rate": success_rate
        }


class BehaviorServicer(behavior_pb2_grpc.BehaviorServiceServicer):
    """行为服务gRPC实现"""
    
    def __init__(self, behavior_service: BehaviorService):
        self.behavior_service = behavior_service
    
    def _convert_pb_to_dict(self, event: behavior_pb2.BehaviorEvent) -> dict:
        """将protobuf事件转换为字典"""
        event_dict = {
            "tenant_id": event.tenant_id,
            "scenario_id": event.scenario_id,
            "user_id": event.user_id,
            "item_id": event.item_id,
            "action_type": behavior_pb2.ActionType.Name(event.action_type),
            "event_id": event.event_id,
            "timestamp": event.timestamp
        }
        
        # 上下文信息
        if event.HasField("context"):
            event_dict["context"] = {
                "device_type": behavior_pb2.DeviceType.Name(event.context.device_type),
                "os": event.context.os,
                "location": event.context.location,
                "ip": event.context.ip,
                "user_agent": event.context.user_agent
            }
        
        # 实验信息
        if event.experiment_id:
            event_dict["experiment_id"] = event.experiment_id
        if event.experiment_group:
            event_dict["experiment_group"] = event.experiment_group
        
        # 位置
        if event.position:
            event_dict["position"] = event.position
        
        # 额外数据
        if event.extra_data:
            event_dict["extra_data"] = dict(event.extra_data)
        
        return event_dict
    
    async def TrackEvent(self, request, context):
        """采集单个行为事件"""
        try:
            event_dict = self._convert_pb_to_dict(request.event)
            success, msg = await self.behavior_service.track_event(event_dict)
            
            return behavior_pb2.TrackEventResponse(
                success=success,
                event_id=msg if success else "",
                message="Success" if success else msg
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Track event failed: {str(e)}")
            return behavior_pb2.TrackEventResponse(success=False, message=str(e))
    
    async def TrackBatch(self, request, context):
        """批量采集行为事件"""
        try:
            events = [self._convert_pb_to_dict(event) for event in request.events]
            succeeded, failed, errors = await self.behavior_service.track_batch(events)
            
            return behavior_pb2.TrackBatchResponse(
                success=(failed == 0),
                total=len(events),
                succeeded=succeeded,
                failed=failed,
                errors=errors
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Track batch failed: {str(e)}")
            return behavior_pb2.TrackBatchResponse(success=False, total=0)
    
    async def GetStats(self, request, context):
        """获取统计信息"""
        try:
            stats = self.behavior_service.get_stats()
            return behavior_pb2.GetStatsResponse(
                total_events=stats["total_events"],
                kafka_success=stats["kafka_success"],
                kafka_failed=stats["kafka_failed"],
                rejected=stats["rejected"],
                success_rate=stats["success_rate"]
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Get stats failed: {str(e)}")
            return behavior_pb2.GetStatsResponse()
    
    async def HealthCheck(self, request, context):
        """健康检查"""
        try:
            kafka_available = self.behavior_service.kafka_producer is not None
            stats = self.behavior_service.get_stats()
            
            stats_response = behavior_pb2.GetStatsResponse(
                total_events=stats["total_events"],
                kafka_success=stats["kafka_success"],
                kafka_failed=stats["kafka_failed"],
                rejected=stats["rejected"],
                success_rate=stats["success_rate"]
            )
            
            status = "healthy" if kafka_available else "degraded"
            
            return behavior_pb2.HealthCheckResponse(
                status=status,
                kafka_available=kafka_available,
                stats=stats_response
            )
        except Exception as e:
            return behavior_pb2.HealthCheckResponse(
                status="unhealthy",
                kafka_available=False
            )


async def serve():
    """启动gRPC服务"""
    config = ServiceConfig()
    host = os.getenv("GRPC_HOST", "0.0.0.0")
    port = int(os.getenv("GRPC_PORT", "8086"))
    
    # 连接Kafka
    kafka_bootstrap_servers = config.kafka_bootstrap_servers
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        compression_type="gzip"
    )
    await kafka_producer.start()
    
    behavior_service = BehaviorService(kafka_producer)
    
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=20),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )
    
    behavior_pb2_grpc.add_BehaviorServiceServicer_to_server(
        BehaviorServicer(behavior_service),
        server
    )
    
    server.add_insecure_port(f"{host}:{port}")
    await server.start()
    
    print(f"[BehaviorService] gRPC服务启动于 {host}:{port}")
    print(f"[BehaviorService] Kafka: {kafka_bootstrap_servers}")
    
    try:
        await server.wait_for_termination()
    finally:
        await kafka_producer.stop()


if __name__ == "__main__":
    asyncio.run(serve())
