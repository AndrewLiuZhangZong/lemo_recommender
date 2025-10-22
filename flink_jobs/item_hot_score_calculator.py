"""
Flink Job 2: 物品热度实时计算
功能：从Kafka消费用户行为数据，实时计算物品热度，写入Redis
"""
from typing import Dict, Any
from datetime import datetime, timedelta
import math


class ItemHotScoreCalculator:
    """
    物品热度实时计算
    
    数据流:
    Kafka (user-behaviors) → Flink滑动窗口聚合 → Redis ZSET
    
    窗口: 1小时滑动窗口，滑动步长15分钟
    分组: tenant_id + scenario_id + item_id
    
    热度算法:
    hot_score = (浏览量 * 1 + 点击量 * 2 + 点赞量 * 3 + 分享量 * 5) * 时间衰减系数
    时间衰减: decay = exp(-λ * 天数), λ = 0.1
    """
    
    def __init__(self, kafka_servers: str, redis_url: str):
        self.kafka_servers = kafka_servers
        self.redis_url = redis_url
        
        # 行为权重
        self.action_weights = {
            'impression': 0.5,
            'view': 1.0,
            'click': 2.0,
            'like': 3.0,
            'favorite': 4.0,
            'share': 5.0,
            'comment': 4.0
        }
        
        # 时间衰减系数
        self.decay_lambda = 0.1
    
    def run(self):
        """
        运行Flink作业
        
        伪代码实现（使用PyFlink API）:
        
        ```python
        from pyflink.datastream import StreamExecutionEnvironment
        from pyflink.datastream.window import SlidingProcessingTimeWindows
        from pyflink.common import Time
        
        # 1. 创建执行环境
        env = StreamExecutionEnvironment.get_execution_environment()
        
        # 2. 从Kafka读取
        behaviors = env.add_source(
            FlinkKafkaConsumer(
                topics=['user-behaviors-*'],
                deserialization_schema=JsonDeserializationSchema(),
                properties={
                    'bootstrap.servers': self.kafka_servers,
                    'group.id': 'item-hot-score-calculator'
                }
            )
        )
        
        # 3. 按物品分组，滑动窗口聚合
        hot_scores = (
            behaviors
            .key_by(lambda x: (x['tenant_id'], x['scenario_id'], x['item_id']))
            .window(
                SlidingProcessingTimeWindows.of(
                    Time.hours(1),      # 窗口大小
                    Time.minutes(15)    # 滑动步长
                )
            )
            .aggregate(HotScoreAggregateFunction(self.action_weights, self.decay_lambda))
        )
        
        # 4. 写入Redis ZSET
        hot_scores.add_sink(
            RedisZSetSink(
                connection_string=self.redis_url,
                key_template='hot:items:{tenant_id}:{scenario_id}',
                score_field='hot_score',
                member_field='item_id',
                max_size=1000  # 只保留Top 1000
            )
        )
        
        # 5. 发送到下游Topic
        hot_scores.add_sink(
            FlinkKafkaProducer(
                topic='item-stats-updates',
                serialization_schema=JsonSerializationSchema()
            )
        )
        
        # 6. 执行作业
        env.execute("Item Hot Score Real-time Calculator")
        ```
        """
        print("=" * 60)
        print("  Flink Job: 物品热度实时计算")
        print("=" * 60)
        print()
        print("📊 作业配置:")
        print(f"  - Kafka: {self.kafka_servers}")
        print(f"  - 窗口: 1小时滑动窗口（步长15分钟）")
        print(f"  - 输出: Redis ZSET + Kafka")
        print()
        print("🔥 热度算法:")
        print("  hot_score = Σ(行为权重) × 时间衰减")
        print(f"  - 行为权重: {self.action_weights}")
        print(f"  - 时间衰减: exp(-{self.decay_lambda} × 天数)")
        print()
        print("💡 待实现功能:")
        print("  1. 从Kafka消费用户行为")
        print("  2. 按(tenant_id, scenario_id, item_id)分组")
        print("  3. 1小时滑动窗口聚合:")
        print("     - 统计各类行为数量")
        print("     - 计算加权热度分数")
        print("     - 应用时间衰减")
        print("  4. 写入Redis ZSET (hot:items:{tenant_id}:{scenario_id})")
        print("  5. 只保留Top 1000热门物品")
        print("  6. 发送到item-stats-updates Topic")
        print()
        print("🚀 启动命令:")
        print("  python flink_jobs/item_hot_score_calculator.py")
        print()


class HotScoreAggregateFunction:
    """物品热度聚合函数"""
    
    def __init__(self, action_weights: Dict[str, float], decay_lambda: float):
        self.action_weights = action_weights
        self.decay_lambda = decay_lambda
    
    def aggregate(self, behaviors: list[Dict[str, Any]]) -> Dict[str, Any]:
        """
        聚合计算物品热度
        
        Args:
            behaviors: 窗口内的行为列表
            
        Returns:
            物品热度数据
        """
        if not behaviors:
            return {}
        
        # 基本信息
        first_behavior = behaviors[0]
        tenant_id = first_behavior['tenant_id']
        scenario_id = first_behavior['scenario_id']
        item_id = first_behavior['item_id']
        
        # 统计各类行为
        action_counts = {}
        for behavior in behaviors:
            action_type = behavior['action_type']
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        # 计算加权分数
        weighted_score = sum(
            action_counts.get(action, 0) * weight
            for action, weight in self.action_weights.items()
        )
        
        # 时间衰减（假设物品最新行为时间）
        latest_timestamp = max(
            datetime.fromisoformat(b['timestamp'])
            for b in behaviors
        )
        age_days = (datetime.utcnow() - latest_timestamp).total_seconds() / 86400
        decay_factor = math.exp(-self.decay_lambda * age_days)
        
        # 最终热度分数
        hot_score = weighted_score * decay_factor
        
        return {
            'tenant_id': tenant_id,
            'scenario_id': scenario_id,
            'item_id': item_id,
            'hot_score': round(hot_score, 2),
            'action_counts': action_counts,
            'window_end': datetime.utcnow().isoformat()
        }


if __name__ == '__main__':
    # 配置
    kafka_servers = 'localhost:9092'
    redis_url = 'redis://:redis_password_2024@localhost:6379/0'
    
    # 运行作业
    calculator = ItemHotScoreCalculator(kafka_servers, redis_url)
    calculator.run()

