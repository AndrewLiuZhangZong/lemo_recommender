"""
行为采集服务 - v2.0架构

设计原则：
1. 不写MongoDB（行为数据直接到Kafka→ClickHouse）
2. 强制tenant_id验证（SaaS多租户隔离）
3. 支持批量采集（高吞吐）
4. 异步非阻塞（不影响用户体验）
5. 支持场景特定字段验证（可选）
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
import logging

logger = logging.getLogger(__name__)


class BehaviorService:
    """行为采集服务"""
    
    def __init__(self, kafka_producer=None, tracking_service=None):
        """
        初始化行为采集服务
        
        Args:
            kafka_producer: Kafka生产者实例（可选，用于实时流处理）
            tracking_service: 场景埋点配置服务（可选，用于场景数据验证）
        """
        self.kafka_producer = kafka_producer
        self.tracking_service = tracking_service
        self._stats = {
            "total_events": 0,
            "kafka_success": 0,
            "kafka_failed": 0,
            "rejected": 0,
            "validation_warnings": 0
        }
        
        # 场景配置缓存（tenant_id:scenario_id -> config）
        self._config_cache: Dict[str, Dict[str, Any]] = {}
    
    async def track_event(
        self,
        event: Dict[str, Any],
        validate_only: bool = False,
        validate_scenario_data: bool = True
    ) -> Dict[str, Any]:
        """
        采集单个用户行为事件
        
        Args:
            event: 行为事件数据
            validate_only: 仅验证不发送（用于调试）
            validate_scenario_data: 是否验证场景特定数据（默认True）
        
        Returns:
            {
                "success": bool,
                "event_id": str,
                "message": str,
                "validation_warnings": List[str]  # 验证警告（可选）
            }
        
        Raises:
            ValueError: tenant_id缺失或数据验证失败
        """
        # 1. 强制tenant_id验证（SaaS隔离） 🔒
        if not event.get('tenant_id'):
            self._stats["rejected"] += 1
            raise ValueError(
                "tenant_id is required for SaaS system. "
                "All events must include tenant_id for data isolation."
            )
        
        # 2. 验证必填字段
        self._validate_event(event)
        
        # 3. 补充event_id和timestamp
        if not event.get('event_id'):
            event['event_id'] = f"evt_{uuid.uuid4().hex[:16]}"
        
        if not event.get('timestamp'):
            event['timestamp'] = int(datetime.now().timestamp() * 1000)  # 毫秒时间戳
        
        # 4. 场景数据验证（可选）
        validation_warnings = []
        if validate_scenario_data:
            validation_result = await self._validate_scenario_data(event)
            if validation_result:
                validation_warnings = validation_result.get("warnings", [])
                if validation_result.get("errors"):
                    self._stats["validation_warnings"] += 1
                    logger.warning(
                        f"Scenario data validation warnings for {event['scenario_id']}: "
                        f"{validation_result['errors']}"
                    )
        
        # 5. 仅验证模式
        if validate_only:
            return {
                "success": True,
                "event_id": event['event_id'],
                "message": "Validation passed (not sent to Kafka)",
                "validation_warnings": validation_warnings
            }
        
        # 6. 发送到Kafka
        success = await self._send_to_kafka(event)
        
        # 7. 更新统计
        self._stats["total_events"] += 1
        if success:
            self._stats["kafka_success"] += 1
        else:
            self._stats["kafka_failed"] += 1
        
        result = {
            "success": success,
            "event_id": event['event_id'],
            "message": "Event tracked successfully" if success else "Event queued (Kafka unavailable)"
        }
        
        if validation_warnings:
            result["validation_warnings"] = validation_warnings
        
        return result
    
    async def track_batch(
        self,
        events: List[Dict[str, Any]],
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """
        批量采集用户行为事件
        
        Args:
            events: 行为事件列表
            validate_only: 仅验证不发送
        
        Returns:
            {
                "success": bool,
                "total": int,
                "succeeded": int,
                "failed": int,
                "errors": List[str]
            }
        """
        if not events:
            return {
                "success": False,
                "total": 0,
                "succeeded": 0,
                "failed": 0,
                "errors": ["No events provided"]
            }
        
        results = {
            "success": True,
            "total": len(events),
            "succeeded": 0,
            "failed": 0,
            "errors": []
        }
        
        for i, event in enumerate(events):
            try:
                result = await self.track_event(event, validate_only)
                if result["success"]:
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Event {i}: {str(e)}")
                results["success"] = False
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取采集统计信息
        
        Returns:
            {
                "total_events": int,
                "kafka_success": int,
                "kafka_failed": int,
                "rejected": int,
                "success_rate": float
            }
        """
        total = self._stats["total_events"]
        success_rate = (
            self._stats["kafka_success"] / total * 100
            if total > 0 else 0
        )
        
        return {
            **self._stats,
            "success_rate": round(success_rate, 2)
        }
    
    def _validate_event(self, event: Dict[str, Any]) -> None:
        """
        验证事件数据
        
        必填字段：
        - tenant_id（已在track_event中检查）
        - scenario_id
        - user_id
        - item_id
        - action_type
        - context.device_type
        """
        required_fields = [
            'scenario_id',
            'user_id',
            'item_id',
            'action_type'
        ]
        
        missing = [f for f in required_fields if not event.get(f)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        # 验证context
        context = event.get('context', {})
        if not isinstance(context, dict):
            raise ValueError("context must be a dictionary")
        
        if not context.get('device_type'):
            raise ValueError("context.device_type is required")
        
        # 验证action_type是否合法
        valid_actions = [
            'impression', 'click', 'view',
            'play', 'play_end', 'read', 'read_end', 'learn', 'complete',
            'like', 'dislike', 'favorite', 'share', 'comment', 'follow',
            'add_cart', 'order', 'payment', 'purchase',
            'not_interest', 'pause', 'repeat', 'download',
            'trial', 'note', 'ask', 'review', 'add_playlist'
        ]
        
        if event['action_type'] not in valid_actions:
            logger.warning(f"Unknown action_type: {event['action_type']}")
    
    async def _send_to_kafka(self, event: Dict[str, Any]) -> bool:
        """
        发送事件到Kafka
        
        Topic命名规则: user-behaviors-{tenant_id}
        Key: user_id（保证同一用户的事件有序）
        
        Args:
            event: 事件数据
        
        Returns:
            bool: 是否发送成功
        """
        if not self.kafka_producer:
            logger.warning("Kafka producer not configured, event not sent")
            return False
        
        try:
            # Topic: user-behaviors-{tenant_id}
            topic = f"user-behaviors-{event['tenant_id']}"
            
            # 准备消息（确保JSON序列化）
            message = {
                "event_id": event['event_id'],
                "tenant_id": event['tenant_id'],
                "scenario_id": event['scenario_id'],
                "user_id": event['user_id'],
                "item_id": event['item_id'],
                "action_type": event['action_type'],
                "context": event.get('context', {}),
                "extra_data": json.dumps(event.get('extra_data', {})),
                "timestamp": event['timestamp'],
                "experiment_id": event.get('experiment_id', ''),
                "experiment_group": event.get('experiment_group', ''),
            }
            
            # 添加场景特定字段
            if 'position' in event:
                message['position'] = event['position']
            if 'duration' in event:
                message['duration'] = event['duration']
            if 'watch_duration' in event:
                message['watch_duration'] = event['watch_duration']
            if 'completion_rate' in event:
                message['completion_rate'] = event['completion_rate']
            
            # 发送到Kafka（异步，不阻塞）
            await self.kafka_producer.send(
                topic=topic,
                value=message,
                key=event['user_id']  # Key用于分区，保证有序
            )
            
            logger.info(
                f"[Kafka] Event sent: {topic} | "
                f"{event['user_id']}/{event['action_type']}/{event['item_id']}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"[Kafka] Failed to send event: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "kafka_available": bool,
                "stats": dict
            }
        """
        kafka_available = self.kafka_producer is not None
        
        # 判断状态
        if kafka_available:
            status = "healthy"
        else:
            status = "degraded"  # Kafka不可用但服务可用
        
        return {
            "status": status,
            "kafka_available": kafka_available,
            "stats": self.get_stats()
        }
    
    async def _validate_scenario_data(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        验证场景特定数据
        
        Args:
            event: 行为事件数据
        
        Returns:
            验证结果（包含warnings和errors），如果没有tracking_service返回None
        """
        if not self.tracking_service:
            return None
        
        tenant_id = event.get("tenant_id")
        scenario_id = event.get("scenario_id")
        scenario_data = event.get("scenario_data", {})
        
        # 如果没有场景数据，跳过验证
        if not scenario_data:
            return None
        
        # 从缓存获取配置
        cache_key = f"{tenant_id}:{scenario_id}"
        config = self._config_cache.get(cache_key)
        
        # 如果缓存没有，从数据库获取
        if not config:
            try:
                config = await self.tracking_service.get_config(
                    tenant_id=tenant_id,
                    scenario_id=scenario_id
                )
                if config:
                    self._config_cache[cache_key] = config
            except Exception as e:
                logger.warning(f"Failed to get tracking config: {e}")
                return None
        
        # 如果没有配置，跳过验证
        if not config:
            return None
        
        # 使用验证器验证
        from app.services.scenario_tracking.validator import TrackingDataValidator
        
        validator = TrackingDataValidator(config)
        validation_result = validator.validate(scenario_data, strict=False)
        
        if not validation_result.is_valid:
            return {
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "missing_fields": validation_result.missing_fields,
                "invalid_fields": validation_result.invalid_fields
            }
        
        return {
            "errors": [],
            "warnings": validation_result.warnings
        }
    
    def clear_config_cache(self):
        """清空配置缓存"""
        self._config_cache.clear()
        logger.info("Tracking config cache cleared")

