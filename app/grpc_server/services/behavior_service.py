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
        
        # 场景特定数据（新增）
        if event_proto.HasField('scenario_data'):
            scenario_data = event_proto.scenario_data
            which = scenario_data.WhichOneof('data')
            
            if which == 'video_data':
                event['scenario_data'] = self._video_data_to_dict(scenario_data.video_data)
            elif which == 'ecommerce_data':
                event['scenario_data'] = self._ecommerce_data_to_dict(scenario_data.ecommerce_data)
            elif which == 'news_data':
                event['scenario_data'] = self._news_data_to_dict(scenario_data.news_data)
            elif which == 'music_data':
                event['scenario_data'] = self._music_data_to_dict(scenario_data.music_data)
            elif which == 'education_data':
                event['scenario_data'] = self._education_data_to_dict(scenario_data.education_data)
            elif which == 'custom_data':
                event['scenario_data'] = self._struct_to_dict(scenario_data.custom_data)
        
        # 额外数据（Struct转dict）
        if event_proto.extra_data:
            event["extra_data"] = self._struct_to_dict(event_proto.extra_data)
        
        return event
    
    def _video_data_to_dict(self, video_data) -> dict:
        """转换视频场景数据"""
        result = {}
        if video_data.duration:
            result["duration"] = video_data.duration
        if video_data.watch_duration:
            result["watch_duration"] = video_data.watch_duration
        if video_data.completion_rate:
            result["completion_rate"] = video_data.completion_rate
        if video_data.video_quality:
            result["video_quality"] = video_data.video_quality
        if video_data.HasField('is_fullscreen'):
            result["is_fullscreen"] = video_data.is_fullscreen
        if video_data.HasField('is_muted'):
            result["is_muted"] = video_data.is_muted
        if video_data.playback_speed:
            result["playback_speed"] = video_data.playback_speed
        if video_data.seek_positions:
            result["seek_positions"] = list(video_data.seek_positions)
        if video_data.buffer_time:
            result["buffer_time"] = video_data.buffer_time
        return result
    
    def _ecommerce_data_to_dict(self, ecommerce_data) -> dict:
        """转换电商场景数据"""
        result = {}
        if ecommerce_data.price:
            result["price"] = ecommerce_data.price
        if ecommerce_data.currency:
            result["currency"] = ecommerce_data.currency
        if ecommerce_data.quantity:
            result["quantity"] = ecommerce_data.quantity
        if ecommerce_data.discount:
            result["discount"] = ecommerce_data.discount
        if ecommerce_data.category_path:
            result["category_path"] = ecommerce_data.category_path
        if ecommerce_data.brand:
            result["brand"] = ecommerce_data.brand
        if ecommerce_data.sku_id:
            result["sku_id"] = ecommerce_data.sku_id
        if ecommerce_data.product_tags:
            result["product_tags"] = list(ecommerce_data.product_tags)
        if ecommerce_data.stock_count:
            result["stock_count"] = ecommerce_data.stock_count
        if ecommerce_data.coupon_id:
            result["coupon_id"] = ecommerce_data.coupon_id
        return result
    
    def _news_data_to_dict(self, news_data) -> dict:
        """转换新闻场景数据"""
        result = {}
        if news_data.read_duration:
            result["read_duration"] = news_data.read_duration
        if news_data.read_progress:
            result["read_progress"] = news_data.read_progress
        if news_data.word_count:
            result["word_count"] = news_data.word_count
        if news_data.news_type:
            result["news_type"] = news_data.news_type
        if news_data.source:
            result["source"] = news_data.source
        if news_data.author:
            result["author"] = news_data.author
        if news_data.keywords:
            result["keywords"] = list(news_data.keywords)
        if news_data.HasField('is_breaking_news'):
            result["is_breaking_news"] = news_data.is_breaking_news
        if news_data.publish_time:
            result["publish_time"] = news_data.publish_time
        return result
    
    def _music_data_to_dict(self, music_data) -> dict:
        """转换音乐场景数据"""
        result = {}
        if music_data.duration:
            result["duration"] = music_data.duration
        if music_data.play_duration:
            result["play_duration"] = music_data.play_duration
        if music_data.artist:
            result["artist"] = music_data.artist
        if music_data.album:
            result["album"] = music_data.album
        if music_data.genre:
            result["genre"] = music_data.genre
        if music_data.bpm:
            result["bpm"] = music_data.bpm
        if music_data.language:
            result["language"] = music_data.language
        if music_data.HasField('is_vip_only'):
            result["is_vip_only"] = music_data.is_vip_only
        if music_data.audio_quality:
            result["audio_quality"] = music_data.audio_quality
        return result
    
    def _education_data_to_dict(self, education_data) -> dict:
        """转换教育场景数据"""
        result = {}
        if education_data.course_id:
            result["course_id"] = education_data.course_id
        if education_data.chapter_id:
            result["chapter_id"] = education_data.chapter_id
        if education_data.lesson_duration:
            result["lesson_duration"] = education_data.lesson_duration
        if education_data.study_duration:
            result["study_duration"] = education_data.study_duration
        if education_data.progress:
            result["progress"] = education_data.progress
        if education_data.exercise_count:
            result["exercise_count"] = education_data.exercise_count
        if education_data.correct_count:
            result["correct_count"] = education_data.correct_count
        if education_data.score:
            result["score"] = education_data.score
        if education_data.difficulty_level:
            result["difficulty_level"] = education_data.difficulty_level
        if education_data.HasField('is_certificate_course'):
            result["is_certificate_course"] = education_data.is_certificate_course
        return result

