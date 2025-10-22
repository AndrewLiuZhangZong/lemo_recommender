"""
Flink Job 2: 物品热度实时计算
功能：从Kafka消费用户行为数据，实时计算物品热度，写入Redis
"""
import json
import sys
import math
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from pyflink.datastream import StreamExecutionEnvironment
    from pyflink.datastream.window import SlidingProcessingTimeWindows
    from pyflink.common import Time, WatermarkStrategy
    from pyflink.datastream.functions import ProcessWindowFunction
    from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
    from pyflink.common.serialization import SimpleStringSchema
    PYFLINK_AVAILABLE = True
except ImportError:
    PYFLINK_AVAILABLE = False
    print("⚠️  PyFlink未安装，使用模拟模式")


class HotScoreCalculator(ProcessWindowFunction):
    """物品热度计算函数"""
    
    def __init__(self, action_weights, decay_lambda):
        self.action_weights = action_weights
        self.decay_lambda = decay_lambda
    
    def process(self, key, context, elements):
        """
        计算窗口内物品的热度分数
        
        Args:
            key: (tenant_id, scenario_id, item_id)
            context: 窗口上下文
            elements: 窗口内的所有行为
        """
        tenant_id, scenario_id, item_id = key
        
        # 统计各类行为数量
        action_counts = defaultdict(int)
        total_duration = 0
        user_set = set()
        
        for behavior in elements:
            action_type = behavior.get('action_type')
            action_counts[action_type] += 1
            
            # 统计用户数（去重）
            user_set.add(behavior.get('user_id'))
            
            # 统计观看时长
            extra = behavior.get('extra', {})
            if 'duration' in extra:
                try:
                    total_duration += float(extra['duration'])
                except:
                    pass
        
        # 计算基础热度分数
        base_score = 0
        for action_type, count in action_counts.items():
            weight = self.action_weights.get(action_type, 1.0)
            base_score += count * weight
        
        # 时间衰减（基于窗口结束时间）
        now = datetime.now()
        window_end = datetime.fromtimestamp(context.window().end / 1000)
        days_ago = (now - window_end).days
        decay_factor = math.exp(-self.decay_lambda * days_ago)
        
        # 最终热度分数
        hot_score = base_score * decay_factor
        
        # 构造结果
        result = {
            'tenant_id': tenant_id,
            'scenario_id': scenario_id,
            'item_id': item_id,
            'hot_score': round(hot_score, 2),
            'stats': {
                'view_count': action_counts.get('view', 0),
                'click_count': action_counts.get('click', 0),
                'like_count': action_counts.get('like', 0),
                'share_count': action_counts.get('share', 0),
                'unique_users': len(user_set),
                'avg_duration': round(total_duration / len(list(elements)), 2) if elements else 0
            },
            'window_start': context.window().start,
            'window_end': context.window().end,
            'calculated_at': datetime.utcnow().isoformat()
        }
        
        yield json.dumps(result, ensure_ascii=False)


class ItemHotScoreCalculator:
    """物品热度实时计算"""
    
    def __init__(
        self,
        kafka_servers: str = "localhost:9092",
        redis_url: str = "redis://:redis_password@localhost:6379/0"
    ):
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
        """运行Flink作业"""
        
        if not PYFLINK_AVAILABLE:
            print("=" * 60)
            print("  Flink Job: 物品热度实时计算 (模拟模式)")
            print("=" * 60)
            print()
            print("📊 作业配置:")
            print(f"  - Kafka: {self.kafka_servers}")
            print(f"  - Redis: {self.redis_url}")
            print(f"  - 行为权重: {self.action_weights}")
            print(f"  - 衰减系数: {self.decay_lambda}")
            print()
            print("⚠️  请安装PyFlink:")
            print("  pip install apache-flink")
            print()
            return
        
        print("=" * 60)
        print("  Flink Job: 物品热度实时计算")
        print("=" * 60)
        
        # 1. 创建执行环境
        env = StreamExecutionEnvironment.get_execution_environment()
        env.set_parallelism(4)
        
        # 2. 从Kafka读取用户行为数据
        kafka_source = KafkaSource.builder() \
            .set_bootstrap_servers(self.kafka_servers) \
            .set_topics("user-behaviors-.*") \
            .set_group_id("item-hot-score-calculator") \
            .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
            .set_value_only_deserializer(SimpleStringSchema()) \
            .build()
        
        behaviors = env.from_source(
            kafka_source,
            WatermarkStrategy.no_watermarks(),
            "Kafka User Behaviors Source"
        )
        
        # 3. 解析JSON
        parsed_behaviors = behaviors.map(
            lambda x: json.loads(x),
            output_type=dict
        )
        
        # 4. 按物品分组，滑动窗口聚合
        hot_scores = (
            parsed_behaviors
            .key_by(lambda x: (x['tenant_id'], x['scenario_id'], x['item_id']))
            .window(SlidingProcessingTimeWindows.of(
                Time.hours(1),      # 窗口大小: 1小时
                Time.minutes(15)    # 滑动步长: 15分钟
            ))
            .process(HotScoreCalculator(self.action_weights, self.decay_lambda))
        )
        
        # 5. 写入Redis ZSET
        def write_to_redis(score_json):
            """写入Redis的函数"""
            try:
                import redis
                score_data = json.loads(score_json)
                
                r = redis.from_url(self.redis_url)
                
                # ZSET key: hot:items:{tenant_id}:{scenario_id}
                redis_key = f"hot:items:{score_data['tenant_id']}:{score_data['scenario_id']}"
                
                # 添加到有序集合
                r.zadd(redis_key, {score_data['item_id']: score_data['hot_score']})
                
                # 只保留Top 1000
                r.zremrangebyrank(redis_key, 0, -1001)
                
                # 设置过期时间（2小时）
                r.expire(redis_key, 7200)
                
                print(f"[Redis] 更新物品热度: {score_data['item_id']} = {score_data['hot_score']}")
                
            except Exception as e:
                print(f"[Redis] 写入失败: {e}")
        
        hot_scores.map(write_to_redis)
        
        # 6. 打印到控制台（调试用）
        hot_scores.print()
        
        # 7. 执行作业
        print("\n🚀 启动Flink作业...")
        env.execute("Item Hot Score Real-time Calculator")


def main():
    """主函数"""
    import os
    
    kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    redis_url = os.getenv('REDIS_URL', 'redis://:redis_password@localhost:6379/0')
    
    calculator = ItemHotScoreCalculator(
        kafka_servers=kafka_servers,
        redis_url=redis_url
    )
    
    try:
        calculator.run()
    except KeyboardInterrupt:
        print("\n\n收到中断信号，停止作业...")
    except Exception as e:
        print(f"\n\n❌ 作业失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
