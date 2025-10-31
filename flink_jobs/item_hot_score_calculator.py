"""
Flink Job 2: 物品热度实时计算（配置驱动版）
功能：从Kafka消费用户行为数据，实时计算物品热度，写入Redis
特性：根据 MongoDB Scenario 配置动态应用计算参数
"""
import json
import sys
import os
import math
import threading
import time
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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

# 导入配置加载器
try:
    from app.services.realtime.config_loader import RealtimeConfigLoader
except ImportError:
    print("⚠️  无法导入 RealtimeConfigLoader，请检查项目路径")
    RealtimeConfigLoader = None


class HotScoreCalculator(ProcessWindowFunction):
    """物品热度计算函数（配置驱动版）"""
    
    def __init__(self, config_loader):
        """
        Args:
            config_loader: RealtimeConfigLoader 实例，用于动态获取配置
        """
        self.config_loader = config_loader
    
    def process(self, key, context, elements):
        """
        计算窗口内物品的热度分数
        
        Args:
            key: (tenant_id, scenario_id, item_id)
            context: 窗口上下文
            elements: 窗口内的所有行为
        """
        tenant_id, scenario_id, item_id = key
        
        # 🔥 动态获取配置（根据租户和场景）
        action_weights = self.config_loader.get_action_weights(tenant_id, scenario_id)
        decay_lambda = self.config_loader.get_decay_lambda(tenant_id, scenario_id)
        
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
        
        # 计算基础热度分数（使用动态配置）
        base_score = 0
        for action_type, count in action_counts.items():
            weight = action_weights.get(action_type, 1.0)
            base_score += count * weight
        
        # 时间衰减（基于窗口结束时间，使用动态配置）
        now = datetime.now()
        window_end = datetime.fromtimestamp(context.window().end / 1000)
        days_ago = (now - window_end).days
        decay_factor = math.exp(-decay_lambda * days_ago)
        
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
    """物品热度实时计算（配置驱动版）"""
    
    def __init__(
        self,
        kafka_servers: str = "localhost:9092",
        redis_url: str = "redis://:redis_password@localhost:6379/0",
        mongodb_url: str = "mongodb://localhost:27017/",
        mongodb_database: str = "lemo_recommender"
    ):
        self.kafka_servers = kafka_servers
        self.redis_url = redis_url
        self.mongodb_url = mongodb_url
        self.mongodb_database = mongodb_database
        
        # 配置加载器
        if RealtimeConfigLoader:
            self.config_loader = RealtimeConfigLoader(mongodb_url, mongodb_database)
            print(f"✅ 配置加载器已初始化")
            
            # 加载配置
            self.config_loader.load_configs()
            
            # 启动配置刷新线程
            self._start_config_refresh_thread()
        else:
            print("⚠️  RealtimeConfigLoader 不可用，将使用默认配置")
            self.config_loader = None
    
    def _start_config_refresh_thread(self):
        """启动配置刷新线程（每5分钟刷新一次）"""
        def refresh():
            while True:
                try:
                    time.sleep(300)  # 5分钟
                    self.config_loader.load_configs()
                    print("🔄 配置已刷新")
                except Exception as e:
                    print(f"⚠️  配置刷新失败: {e}")
        
        thread = threading.Thread(target=refresh, daemon=True)
        thread.start()
        print("✅ 配置刷新线程已启动（每5分钟）")
    
    def run(self):
        """运行Flink作业"""
        
        if not PYFLINK_AVAILABLE:
            print("=" * 70)
            print("  Flink Job: 物品热度实时计算（配置驱动版） - 模拟模式")
            print("=" * 70)
            print()
            print("📊 作业配置:")
            print(f"  - Kafka: {self.kafka_servers}")
            print(f"  - Redis: {self.redis_url}")
            print(f"  - MongoDB: {self.mongodb_url}")
            print(f"  - Database: {self.mongodb_database}")
            if self.config_loader:
                print(f"  - 已加载场景数: {len(self.config_loader.configs)}")
                self.config_loader.print_summary()
            print()
            print("⚠️  请安装PyFlink:")
            print("  pip install apache-flink")
            print()
            return
        
        print("=" * 70)
        print("  Flink Job: 物品热度实时计算（配置驱动版）")
        print("=" * 70)
        
        # 打印配置摘要
        if self.config_loader:
            self.config_loader.print_summary()
        
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
        
        # 4. 按物品分组，滑动窗口聚合（使用配置驱动的计算器）
        hot_scores = (
            parsed_behaviors
            .key_by(lambda x: (x['tenant_id'], x['scenario_id'], x['item_id']))
            .window(SlidingProcessingTimeWindows.of(
                Time.hours(1),      # 窗口大小: 1小时（可通过配置调整）
                Time.minutes(15)    # 滑动步长: 15分钟（可通过配置调整）
            ))
            .process(HotScoreCalculator(self.config_loader))
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
    kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    redis_url = os.getenv('REDIS_URL', 'redis://:redis_password@localhost:6379/0')
    mongodb_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
    mongodb_database = os.getenv('MONGODB_DATABASE', 'lemo_recommender')
    
    print("=" * 70)
    print("启动参数:")
    print(f"  - Kafka: {kafka_servers}")
    print(f"  - Redis: {redis_url}")
    print(f"  - MongoDB: {mongodb_url}")
    print(f"  - Database: {mongodb_database}")
    print("=" * 70)
    
    calculator = ItemHotScoreCalculator(
        kafka_servers=kafka_servers,
        redis_url=redis_url,
        mongodb_url=mongodb_url,
        mongodb_database=mongodb_database
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
