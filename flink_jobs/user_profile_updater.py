"""
Flink Job 1: 用户画像实时更新
功能：从Kafka消费用户行为数据，实时聚合计算用户画像，写入MongoDB和Redis
"""
import json
import sys
from datetime import datetime
from collections import defaultdict

try:
    from pyflink.datastream import StreamExecutionEnvironment
    from pyflink.datastream.window import TumblingProcessingTimeWindows
    from pyflink.common import Time, WatermarkStrategy
    from pyflink.datastream.functions import ProcessWindowFunction, KeyedProcessFunction
    from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
    from pyflink.common.serialization import SimpleStringSchema
    PYFLINK_AVAILABLE = True
except ImportError:
    PYFLINK_AVAILABLE = False
    print("⚠️  PyFlink未安装，使用模拟模式")


class UserProfileAggregator(ProcessWindowFunction):
    """用户画像聚合函数"""
    
    def process(self, key, context, elements):
        """
        聚合窗口内的用户行为，生成用户画像
        
        Args:
            key: (tenant_id, user_id, scenario_id)
            context: 窗口上下文
            elements: 窗口内的所有行为
        """
        tenant_id, user_id, scenario_id = key
        
        # 聚合统计
        stats = {
            'view_count': 0,
            'click_count': 0,
            'like_count': 0,
            'share_count': 0,
            'comment_count': 0,
            'favorite_count': 0,
            'categories': defaultdict(int),
            'tags': defaultdict(int),
            'active_hours': defaultdict(int),
            'viewed_items': []
        }
        
        for behavior in elements:
            action_type = behavior.get('action_type')
            
            # 行为计数
            if action_type == 'view':
                stats['view_count'] += 1
            elif action_type == 'click':
                stats['click_count'] += 1
            elif action_type == 'like':
                stats['like_count'] += 1
            elif action_type == 'share':
                stats['share_count'] += 1
            elif action_type == 'comment':
                stats['comment_count'] += 1
            elif action_type == 'favorite':
                stats['favorite_count'] += 1
            
            # 收集物品信息
            item_id = behavior.get('item_id')
            if item_id:
                stats['viewed_items'].append(item_id)
            
            # 分类统计（从context中提取）
            context_data = behavior.get('context', {})
            if 'category' in context_data:
                stats['categories'][context_data['category']] += 1
            
            # 标签统计
            if 'tags' in context_data:
                for tag in context_data.get('tags', []):
                    stats['tags'][tag] += 1
            
            # 活跃时段
            timestamp = behavior.get('timestamp')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour = dt.hour
                    stats['active_hours'][hour] += 1
                except:
                    pass
        
        # 计算偏好（Top 5）
        top_categories = sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True)[:5]
        top_tags = sorted(stats['tags'].items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 构造用户画像
        profile = {
            'tenant_id': tenant_id,
            'user_id': user_id,
            'scenario_id': scenario_id,
            'stats': {
                'view_count': stats['view_count'],
                'click_count': stats['click_count'],
                'like_count': stats['like_count'],
                'engagement_rate': stats['click_count'] / stats['view_count'] if stats['view_count'] > 0 else 0
            },
            'preferences': {
                'categories': [{'name': cat, 'score': score} for cat, score in top_categories],
                'tags': [{'name': tag, 'score': score} for tag, score in top_tags]
            },
            'active_hours': dict(stats['active_hours']),
            'recent_items': stats['viewed_items'][-20:],  # 最近20个
            'window_start': context.window().start,
            'window_end': context.window().end,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        yield json.dumps(profile, ensure_ascii=False)


class UserProfileUpdater:
    """用户画像实时更新"""
    
    def __init__(
        self,
        kafka_servers: str = "localhost:9092",
        mongodb_url: str = "mongodb://admin:password@localhost:27017",
        redis_url: str = "redis://:redis_password@localhost:6379/0"
    ):
        self.kafka_servers = kafka_servers
        self.mongodb_url = mongodb_url
        self.redis_url = redis_url
    
    def run(self):
        """运行Flink作业"""
        
        if not PYFLINK_AVAILABLE:
            print("=" * 60)
            print("  Flink Job: 用户画像实时更新 (模拟模式)")
            print("=" * 60)
            print()
            print("📊 作业配置:")
            print(f"  - Kafka: {self.kafka_servers}")
            print(f"  - MongoDB: {self.mongodb_url}")
            print(f"  - Redis: {self.redis_url}")
            print()
            print("⚠️  请安装PyFlink:")
            print("  pip install apache-flink")
            print()
            return
        
        print("=" * 60)
        print("  Flink Job: 用户画像实时更新")
        print("=" * 60)
        
        # 1. 创建执行环境
        env = StreamExecutionEnvironment.get_execution_environment()
        env.set_parallelism(4)
        
        # 2. 从Kafka读取用户行为数据
        kafka_source = KafkaSource.builder() \
            .set_bootstrap_servers(self.kafka_servers) \
            .set_topics("user-behaviors-.*")  \
            .set_group_id("user-profile-updater") \
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
        
        # 4. 按用户分组并窗口聚合
        user_profiles = (
            parsed_behaviors
            .key_by(lambda x: (x['tenant_id'], x['user_id'], x['scenario_id']))
            .window(TumblingProcessingTimeWindows.of(Time.minutes(5)))
            .process(UserProfileAggregator())
        )
        
        # 5. 写入MongoDB (使用自定义Sink)
        def write_to_mongodb(profile_json):
            """写入MongoDB的函数"""
            try:
                from pymongo import MongoClient
                profile = json.loads(profile_json)
                
                client = MongoClient(self.mongodb_url)
                db = client['lemo_recommender']
                
                # 更新或插入
                db.user_profiles.update_one(
                    {
                        'tenant_id': profile['tenant_id'],
                        'user_id': profile['user_id'],
                        'scenario_id': profile['scenario_id']
                    },
                    {
                        '$set': profile,
                        '$inc': {'update_count': 1}
                    },
                    upsert=True
                )
                
                print(f"[MongoDB] 更新用户画像: {profile['user_id']}")
                
            except Exception as e:
                print(f"[MongoDB] 写入失败: {e}")
        
        user_profiles.map(write_to_mongodb)
        
        # 6. 写入Redis缓存
        def write_to_redis(profile_json):
            """写入Redis的函数"""
            try:
                import redis
                profile = json.loads(profile_json)
                
                r = redis.from_url(self.redis_url)
                
                cache_key = f"user:profile:{profile['tenant_id']}:{profile['user_id']}:{profile['scenario_id']}"
                r.setex(cache_key, 3600, profile_json)  # 1小时过期
                
                print(f"[Redis] 缓存用户画像: {profile['user_id']}")
                
            except Exception as e:
                print(f"[Redis] 写入失败: {e}")
        
        user_profiles.map(write_to_redis)
        
        # 7. 打印到控制台（调试用）
        user_profiles.print()
        
        # 8. 执行作业
        print("\n🚀 启动Flink作业...")
        env.execute("User Profile Real-time Updater")


def main():
    """主函数"""
    import os
    
    kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    mongodb_url = os.getenv('MONGODB_URL', 'mongodb://admin:password@localhost:27017')
    redis_url = os.getenv('REDIS_URL', 'redis://:redis_password@localhost:6379/0')
    
    updater = UserProfileUpdater(
        kafka_servers=kafka_servers,
        mongodb_url=mongodb_url,
        redis_url=redis_url
    )
    
    try:
        updater.run()
    except KeyboardInterrupt:
        print("\n\n收到中断信号，停止作业...")
    except Exception as e:
        print(f"\n\n❌ 作业失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
