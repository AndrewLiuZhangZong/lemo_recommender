"""
Flink Job 1: 用户画像实时更新
功能：从Kafka消费用户行为数据，实时聚合计算用户画像，写入MongoDB和Redis
"""
from typing import Dict, Any
from datetime import datetime


class UserProfileUpdater:
    """
    用户画像实时更新
    
    数据流:
    Kafka (user-behaviors) → Flink窗口聚合 → MongoDB/Redis
    
    窗口: 5分钟滚动窗口
    分组: tenant_id + user_id + scenario_id
    """
    
    def __init__(self, kafka_servers: str, mongodb_url: str, redis_url: str):
        self.kafka_servers = kafka_servers
        self.mongodb_url = mongodb_url
        self.redis_url = redis_url
    
    def run(self):
        """
        运行Flink作业
        
        伪代码实现（使用PyFlink API）:
        
        ```python
        from pyflink.datastream import StreamExecutionEnvironment
        from pyflink.datastream.window import TumblingProcessingTimeWindows
        from pyflink.common import Time
        
        # 1. 创建执行环境
        env = StreamExecutionEnvironment.get_execution_environment()
        env.set_parallelism(4)
        
        # 2. 从Kafka读取用户行为数据
        behaviors = env.add_source(
            FlinkKafkaConsumer(
                topics=['user-behaviors-*'],  # 订阅所有租户的行为topic
                deserialization_schema=JsonDeserializationSchema(),
                properties={
                    'bootstrap.servers': self.kafka_servers,
                    'group.id': 'user-profile-updater'
                }
            )
        )
        
        # 3. 按用户分组并窗口聚合
        user_profiles = (
            behaviors
            .key_by(lambda x: (x['tenant_id'], x['user_id'], x['scenario_id']))
            .window(TumblingProcessingTimeWindows.of(Time.minutes(5)))
            .aggregate(UserProfileAggregateFunction())
        )
        
        # 4. 写入MongoDB
        user_profiles.add_sink(
            MongoDBSink(
                connection_string=self.mongodb_url,
                database='lemo_recommender',
                collection='user_profiles'
            )
        )
        
        # 5. 写入Redis（缓存）
        user_profiles.add_sink(
            RedisSink(
                connection_string=self.redis_url,
                key_template='user:profile:{tenant_id}:{user_id}:{scenario_id}',
                ttl=3600
            )
        )
        
        # 6. 发送到下游Topic
        user_profiles.add_sink(
            FlinkKafkaProducer(
                topic='user-profile-updates',
                serialization_schema=JsonSerializationSchema()
            )
        )
        
        # 7. 执行作业
        env.execute("User Profile Real-time Updater")
        ```
        """
        print("=" * 60)
        print("  Flink Job: 用户画像实时更新")
        print("=" * 60)
        print()
        print("📊 作业配置:")
        print(f"  - Kafka: {self.kafka_servers}")
        print(f"  - 窗口: 5分钟滚动窗口")
        print(f"  - 输出: MongoDB + Redis + Kafka")
        print()
        print("💡 待实现功能:")
        print("  1. 从Kafka消费用户行为")
        print("  2. 按(tenant_id, user_id, scenario_id)分组")
        print("  3. 5分钟窗口聚合统计:")
        print("     - 观看次数、点赞次数")
        print("     - 偏好分类统计")
        print("     - 活跃时段分析")
        print("  4. 写入MongoDB user_profiles集合")
        print("  5. 写入Redis缓存")
        print("  6. 发送到user-profile-updates Topic")
        print()
        print("🚀 启动命令:")
        print("  python flink_jobs/user_profile_updater.py")
        print()


class UserProfileAggregateFunction:
    """
    用户画像聚合函数
    
    输入: 用户行为流
    输出: 用户画像更新
    """
    
    @staticmethod
    def aggregate(behaviors: list[Dict[str, Any]]) -> Dict[str, Any]:
        """
        聚合用户行为，计算画像特征
        
        Args:
            behaviors: 窗口内的用户行为列表
            
        Returns:
            用户画像更新数据
        """
        if not behaviors:
            return {}
        
        # 基本信息
        first_behavior = behaviors[0]
        tenant_id = first_behavior['tenant_id']
        user_id = first_behavior['user_id']
        scenario_id = first_behavior['scenario_id']
        
        # 统计特征
        features = {
            'total_actions': len(behaviors),
            'action_types': {},
            'categories': {},
            'active_time_slots': {}
        }
        
        for behavior in behaviors:
            # 行为类型统计
            action_type = behavior['action_type']
            features['action_types'][action_type] = \
                features['action_types'].get(action_type, 0) + 1
            
            # 分类偏好（从item metadata获取）
            category = behavior.get('extra', {}).get('category')
            if category:
                features['categories'][category] = \
                    features['categories'].get(category, 0) + 1
            
            # 活跃时段
            timestamp = datetime.fromisoformat(behavior['timestamp'])
            hour = timestamp.hour
            time_slot = 'morning' if 6 <= hour < 12 else \
                       'afternoon' if 12 <= hour < 18 else \
                       'evening' if 18 <= hour < 24 else 'night'
            features['active_time_slots'][time_slot] = \
                features['active_time_slots'].get(time_slot, 0) + 1
        
        # 计算偏好分数
        total_categories = sum(features['categories'].values())
        preferences = {
            'category_scores': {
                cat: count / total_categories
                for cat, count in features['categories'].items()
            }
        }
        
        return {
            'tenant_id': tenant_id,
            'user_id': user_id,
            'scenario_id': scenario_id,
            'features': features,
            'preferences': preferences,
            'updated_at': datetime.utcnow().isoformat()
        }


if __name__ == '__main__':
    # 配置
    kafka_servers = 'localhost:9092'
    mongodb_url = 'mongodb://admin:password@localhost:27017'
    redis_url = 'redis://:redis_password_2024@localhost:6379/0'
    
    # 运行作业
    updater = UserProfileUpdater(kafka_servers, mongodb_url, redis_url)
    updater.run()

