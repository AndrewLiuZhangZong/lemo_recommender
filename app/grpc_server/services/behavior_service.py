"""行为采集 gRPC 服务实现 - v2.0架构"""
import sys
from pathlib import Path

grpc_gen_path = Path(__file__).parent.parent.parent / "grpc_generated" / "python"
sys.path.insert(0, str(grpc_gen_path))

import grpc
from google.protobuf import struct_pb2
from recommender.v1 import behavior_pb2, behavior_pb2_grpc
from app.services.behavior import BehaviorService
from app.core.kafka import get_kafka_producer
from .base_service import BaseServicer
import logging

logger = logging.getLogger(__name__)


class BehaviorServicer(behavior_pb2_grpc.BehaviorServiceServicer, BaseServicer):
    """行为采集 gRPC 服务"""
    
    def __init__(self):
        # 获取Kafka Producer（可能为None，降级模式）
        kafka_producer = get_kafka_producer()
        self.behavior_service = BehaviorService(kafka_producer=kafka_producer)
    
    async def TrackEvent(self, request, context) -> behavior_pb2.TrackEventResponse:
        """
        采集单个行为事件
        
        Args:
            request: TrackEventRequest
            context: gRPC context
        
        Returns:
            TrackEventResponse
        """
        try:
            # 转换proto消息为字典
            event = self._event_proto_to_dict(request.event)
            
            # 调用服务层
            result = await self.behavior_service.track_event(
                event=event,
                validate_only=False
            )
            
            # 构建响应
            response = behavior_pb2.TrackEventResponse()
            response.success = result["success"]
            response.event_id = result.get("event_id", "")
            response.message = result["message"]
            
            return response
            
        except ValueError as e:
            # tenant_id缺失或数据验证失败
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            logger.warning(f"Event validation failed: {e}")
            raise
        except Exception as e:
            # 其他错误
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            logger.error(f"TrackEvent failed: {e}", exc_info=True)
            raise
    
    async def TrackBatch(self, request, context) -> behavior_pb2.TrackBatchResponse:
        """
        批量采集行为事件
        
        Args:
            request: TrackBatchRequest
            context: gRPC context
        
        Returns:
            TrackBatchResponse
        """
        try:
            # 转换所有事件
            events = [self._event_proto_to_dict(event) for event in request.events]
            
            # 调用服务层
            result = await self.behavior_service.track_batch(
                events=events,
                validate_only=False
            )
            
            # 构建响应
            response = behavior_pb2.TrackBatchResponse()
            response.success = result["success"]
            response.total = result["total"]
            response.succeeded = result["succeeded"]
            response.failed = result["failed"]
            response.errors.extend(result.get("errors", []))
            
            return response
            
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            logger.warning(f"Batch validation failed: {e}")
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            logger.error(f"TrackBatch failed: {e}", exc_info=True)
            raise
    
    async def GetStats(self, request, context) -> behavior_pb2.GetStatsResponse:
        """
        获取采集统计信息
        
        Args:
            request: GetStatsRequest
            context: gRPC context
        
        Returns:
            GetStatsResponse
        """
        try:
            # 调用服务层
            stats = self.behavior_service.get_stats()
            
            # 构建响应
            response = behavior_pb2.GetStatsResponse()
            response.total_events = stats["total_events"]
            response.kafka_success = stats["kafka_success"]
            response.kafka_failed = stats["kafka_failed"]
            response.rejected = stats["rejected"]
            response.success_rate = stats["success_rate"]
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            logger.error(f"GetStats failed: {e}", exc_info=True)
            raise
    
    async def HealthCheck(self, request, context) -> behavior_pb2.HealthCheckResponse:
        """
        健康检查
        
        Args:
            request: HealthCheckRequest
            context: gRPC context
        
        Returns:
            HealthCheckResponse
        """
        try:
            # 调用服务层
            health = await self.behavior_service.health_check()
            
            # 构建响应
            response = behavior_pb2.HealthCheckResponse()
            response.status = health["status"]
            response.kafka_available = health["kafka_available"]
            
            # 嵌套统计信息
            stats = health["stats"]
            response.stats.total_events = stats["total_events"]
            response.stats.kafka_success = stats["kafka_success"]
            response.stats.kafka_failed = stats["kafka_failed"]
            response.stats.rejected = stats["rejected"]
            response.stats.success_rate = stats["success_rate"]
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            logger.error(f"HealthCheck failed: {e}", exc_info=True)
            raise
    
    def _event_proto_to_dict(self, event_proto) -> dict:
        """
        将proto消息转换为字典
        
        Args:
            event_proto: BehaviorEvent proto消息
        
        Returns:
            dict: 事件字典
        """
        # ActionType枚举转换为字符串
        action_type_map = {
            behavior_pb2.ACTION_TYPE_IMPRESSION: "impression",
            behavior_pb2.ACTION_TYPE_CLICK: "click",
            behavior_pb2.ACTION_TYPE_VIEW: "view",
            behavior_pb2.ACTION_TYPE_PLAY: "play",
            behavior_pb2.ACTION_TYPE_PLAY_END: "play_end",
            behavior_pb2.ACTION_TYPE_READ: "read",
            behavior_pb2.ACTION_TYPE_READ_END: "read_end",
            behavior_pb2.ACTION_TYPE_LEARN: "learn",
            behavior_pb2.ACTION_TYPE_COMPLETE: "complete",
            behavior_pb2.ACTION_TYPE_LIKE: "like",
            behavior_pb2.ACTION_TYPE_DISLIKE: "dislike",
            behavior_pb2.ACTION_TYPE_FAVORITE: "favorite",
            behavior_pb2.ACTION_TYPE_SHARE: "share",
            behavior_pb2.ACTION_TYPE_COMMENT: "comment",
            behavior_pb2.ACTION_TYPE_FOLLOW: "follow",
            behavior_pb2.ACTION_TYPE_ADD_CART: "add_cart",
            behavior_pb2.ACTION_TYPE_ORDER: "order",
            behavior_pb2.ACTION_TYPE_PAYMENT: "payment",
            behavior_pb2.ACTION_TYPE_PURCHASE: "purchase",
            behavior_pb2.ACTION_TYPE_NOT_INTEREST: "not_interest",
            behavior_pb2.ACTION_TYPE_PAUSE: "pause",
            behavior_pb2.ACTION_TYPE_REPEAT: "repeat",
            behavior_pb2.ACTION_TYPE_DOWNLOAD: "download",
            behavior_pb2.ACTION_TYPE_TRIAL: "trial",
            behavior_pb2.ACTION_TYPE_NOTE: "note",
            behavior_pb2.ACTION_TYPE_ASK: "ask",
            behavior_pb2.ACTION_TYPE_REVIEW: "review",
            behavior_pb2.ACTION_TYPE_ADD_PLAYLIST: "add_playlist",
        }
        
        # DeviceType枚举转换为字符串
        device_type_map = {
            behavior_pb2.DEVICE_TYPE_MOBILE: "mobile",
            behavior_pb2.DEVICE_TYPE_PC: "pc",
            behavior_pb2.DEVICE_TYPE_TABLET: "tablet",
            behavior_pb2.DEVICE_TYPE_TV: "tv",
            behavior_pb2.DEVICE_TYPE_UNKNOWN: "unknown",
        }
        
        # 构建事件字典
        event = {
            "tenant_id": event_proto.tenant_id,
            "scenario_id": event_proto.scenario_id,
            "user_id": event_proto.user_id,
            "item_id": event_proto.item_id,
            "action_type": action_type_map.get(
                event_proto.action_type, 
                "click"  # 默认值
            ),
            "context": {
                "device_type": device_type_map.get(
                    event_proto.context.device_type,
                    "unknown"
                ),
                "os": event_proto.context.os if event_proto.context.os else None,
                "location": event_proto.context.location if event_proto.context.location else None,
                "ip": event_proto.context.ip if event_proto.context.ip else None,
                "user_agent": event_proto.context.user_agent if event_proto.context.user_agent else None,
            }
        }
        
        # 可选字段
        if event_proto.event_id:
            event["event_id"] = event_proto.event_id
        if event_proto.timestamp:
            event["timestamp"] = event_proto.timestamp
        if event_proto.experiment_id:
            event["experiment_id"] = event_proto.experiment_id
        if event_proto.experiment_group:
            event["experiment_group"] = event_proto.experiment_group
        if event_proto.position:
            event["position"] = event_proto.position
        if event_proto.duration:
            event["duration"] = event_proto.duration
        if event_proto.watch_duration:
            event["watch_duration"] = event_proto.watch_duration
        if event_proto.completion_rate:
            event["completion_rate"] = event_proto.completion_rate
        
        # 额外数据（Struct转dict）
        if event_proto.extra_data:
            event["extra_data"] = self._struct_to_dict(event_proto.extra_data)
        
        return event

