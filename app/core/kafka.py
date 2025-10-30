"""
Kafka客户端封装
"""
from typing import Optional, Dict, Any
import json
from datetime import datetime


class KafkaProducer:
    """Kafka生产者封装"""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self._started = False
        
        try:
            from aiokafka import AIOKafkaProducer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # 等待所有副本确认
                compression_type='gzip',
                # 连接和请求超时配置
                request_timeout_ms=30000,  # 请求超时 30秒
                metadata_max_age_ms=60000,  # 元数据最大存活时间 60秒
                # 连接配置
                connections_max_idle_ms=540000,  # 连接最大空闲时间 9分钟
                # API 版本自动检测超时
                api_version_auto_timeout_ms=10000  # API 版本检测超时 10秒
            )
        except ImportError:
            print("[Kafka] aiokafka未安装，使用模拟模式")
            self.producer = None
    
    async def start(self):
        """启动生产者"""
        if self.producer and not self._started:
            try:
                print(f"[Kafka] 正在连接 Kafka: {self.bootstrap_servers}")
                await self.producer.start()
                self._started = True
                print(f"✅ Kafka Producer已启动: {self.bootstrap_servers}")
            except Exception as e:
                print(f"⚠️  Kafka Producer启动失败: {type(e).__name__}: {e}")
                print(f"⚠️  Kafka 服务器: {self.bootstrap_servers}")
                print(f"⚠️  系统将以无 Kafka 模式运行（仅记录日志）")
                self.producer = None
    
    async def stop(self):
        """停止生产者"""
        if self.producer and self._started:
            try:
                await self.producer.stop()
                self._started = False
                print("[Kafka] Producer已停止")
            except Exception as e:
                print(f"[Kafka] Producer停止失败: {e}")
    
    async def send(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None
    ):
        """
        发送消息到Kafka
        
        Args:
            topic: Topic名称
            value: 消息内容（字典，会自动序列化为JSON）
            key: 消息key（可选，用于分区）
        """
        try:
            if self.producer and self._started:
                # 实际发送
                await self.producer.send(topic, value=value, key=key)
                print(f"[Kafka] 发送成功 → {topic}: {json.dumps(value, ensure_ascii=False)[:80]}...")
            else:
                # 模拟模式：仅打印日志
                print(f"[Kafka模拟] 发送消息到 {topic}: {json.dumps(value, ensure_ascii=False)[:100]}")
            
        except Exception as e:
            print(f"[Kafka] 发送失败: {e}")
            # 降级：不阻塞主流程
            pass


class KafkaConsumer:
    """Kafka消费者封装"""
    
    def __init__(
        self,
        topics: list[str],
        bootstrap_servers: str,
        group_id: str
    ):
        self.topics = topics
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer = None
        self._started = False
        
        try:
            from aiokafka import AIOKafkaConsumer
            self.consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',  # 从最新消息开始
                enable_auto_commit=True,
                max_poll_records=100
            )
        except ImportError:
            print("[Kafka] aiokafka未安装，使用模拟模式")
            self.consumer = None
    
    async def start(self):
        """启动消费者"""
        if self.consumer and not self._started:
            try:
                await self.consumer.start()
                self._started = True
                print(f"[Kafka] Consumer已启动: {self.topics} @ {self.group_id}")
            except Exception as e:
                print(f"[Kafka] Consumer启动失败: {e}")
                self.consumer = None
    
    async def stop(self):
        """停止消费者"""
        if self.consumer and self._started:
            try:
                await self.consumer.stop()
                self._started = False
                print("[Kafka] Consumer已停止")
            except Exception as e:
                print(f"[Kafka] Consumer停止失败: {e}")
    
    async def consume(self):
        """
        消费消息（异步迭代器）
        
        Yields:
            消息字典
        """
        if not self.consumer or not self._started:
            print("[Kafka] Consumer未启动，无法消费")
            return
        
        try:
            async for msg in self.consumer:
                yield {
                    'topic': msg.topic,
                    'partition': msg.partition,
                    'offset': msg.offset,
                    'key': msg.key.decode('utf-8') if msg.key else None,
                    'value': msg.value,
                    'timestamp': msg.timestamp
                }
        except Exception as e:
            print(f"[Kafka] 消费失败: {e}")


# Kafka Topic定义
class KafkaTopics:
    """Kafka Topic名称定义"""
    
    @staticmethod
    def user_behaviors(tenant_id: str) -> str:
        """用户行为Topic（按租户分区）"""
        return f"user-behaviors-{tenant_id}"
    
    @staticmethod
    def user_profile_updates() -> str:
        """用户画像更新Topic"""
        return "user-profile-updates"
    
    @staticmethod
    def item_stats_updates() -> str:
        """物品统计更新Topic"""
        return "item-stats-updates"
    
    @staticmethod
    def recommendation_metrics() -> str:
        """推荐指标Topic"""
        return "recommendation-metrics"


# 消息格式定义
class KafkaMessages:
    """Kafka消息格式定义"""
    
    @staticmethod
    def user_behavior(
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        item_id: str,
        action_type: str,
        context: Dict[str, Any],
        extra: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """用户行为消息"""
        return {
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "user_id": user_id,
            "item_id": item_id,
            "action_type": action_type,
            "context": context,
            "extra": extra,
            "timestamp": (timestamp or datetime.utcnow()).isoformat()
        }
    
    @staticmethod
    def user_profile_update(
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        features: Dict[str, Any],
        preferences: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """用户画像更新消息"""
        return {
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "user_id": user_id,
            "features": features,
            "preferences": preferences,
            "timestamp": (timestamp or datetime.utcnow()).isoformat()
        }
    
    @staticmethod
    def item_stats_update(
        tenant_id: str,
        scenario_id: str,
        item_id: str,
        stats: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """物品统计更新消息"""
        return {
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "item_id": item_id,
            "stats": stats,
            "timestamp": (timestamp or datetime.utcnow()).isoformat()
        }


# 全局Kafka Producer实例
_kafka_producer: Optional[KafkaProducer] = None


def get_kafka_producer() -> Optional[KafkaProducer]:
    """
    获取全局Kafka Producer实例
    
    Returns:
        KafkaProducer实例，如果未初始化则返回None
    """
    global _kafka_producer
    return _kafka_producer


def init_kafka_producer(bootstrap_servers: str) -> KafkaProducer:
    """
    初始化全局Kafka Producer
    
    Args:
        bootstrap_servers: Kafka服务器地址，如"localhost:9092"
    
    Returns:
        KafkaProducer实例
    """
    global _kafka_producer
    if _kafka_producer is None:
        _kafka_producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
    return _kafka_producer


async def startup_kafka():
    """
    启动Kafka Producer（应在FastAPI启动时调用）
    """
    global _kafka_producer
    if _kafka_producer:
        await _kafka_producer.start()


async def shutdown_kafka():
    """
    关闭Kafka Producer（应在FastAPI关闭时调用）
    """
    global _kafka_producer
    if _kafka_producer:
        await _kafka_producer.stop()

