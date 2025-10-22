"""
Flink Job 3: 实时指标统计
功能：从Kafka消费用户行为数据，实时计算推荐效果指标，输出到Prometheus
"""
from typing import Dict, Any
from datetime import datetime


class RecommendationMetrics:
    """
    推荐效果实时指标统计
    
    数据流:
    Kafka (user-behaviors) → Flink窗口聚合 → Prometheus Pushgateway
    
    窗口: 1分钟滚动窗口
    分组: tenant_id + scenario_id
    
    指标:
    - CTR (Click-Through Rate): 点击率
    - 平均观看时长
    - 完播率
    - 互动率 (点赞+分享+评论)
    """
    
    def __init__(
        self,
        kafka_servers: str,
        prometheus_pushgateway: str = 'localhost:9091'
    ):
        self.kafka_servers = kafka_servers
        self.prometheus_pushgateway = prometheus_pushgateway
    
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
        
        # 2. 从Kafka读取
        behaviors = env.add_source(
            FlinkKafkaConsumer(
                topics=['user-behaviors-*'],
                deserialization_schema=JsonDeserializationSchema(),
                properties={
                    'bootstrap.servers': self.kafka_servers,
                    'group.id': 'recommendation-metrics'
                }
            )
        )
        
        # 3. 按场景分组，1分钟窗口聚合
        metrics = (
            behaviors
            .key_by(lambda x: (x['tenant_id'], x['scenario_id']))
            .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
            .aggregate(MetricsAggregateFunction())
        )
        
        # 4. 推送到Prometheus
        metrics.add_sink(
            PrometheusPushGatewaySink(
                pushgateway_url=self.prometheus_pushgateway,
                job='recommendation-metrics'
            )
        )
        
        # 5. 发送到Kafka（供其他系统消费）
        metrics.add_sink(
            FlinkKafkaProducer(
                topic='recommendation-metrics',
                serialization_schema=JsonSerializationSchema()
            )
        )
        
        # 6. 执行作业
        env.execute("Recommendation Metrics Real-time")
        ```
        """
        print("=" * 60)
        print("  Flink Job: 推荐指标实时统计")
        print("=" * 60)
        print()
        print("📊 作业配置:")
        print(f"  - Kafka: {self.kafka_servers}")
        print(f"  - 窗口: 1分钟滚动窗口")
        print(f"  - 输出: Prometheus Pushgateway")
        print()
        print("📈 统计指标:")
        print("  1. CTR (点击率) = 点击数 / 曝光数")
        print("  2. 平均观看时长 = Σ观看时长 / 观看数")
        print("  3. 完播率 = 完整观看数 / 观看数")
        print("  4. 互动率 = (点赞+分享+评论) / 曝光数")
        print("  5. 转化率 = 转化数 / 曝光数")
        print()
        print("💡 待实现功能:")
        print("  1. 从Kafka消费用户行为")
        print("  2. 按(tenant_id, scenario_id)分组")
        print("  3. 1分钟窗口聚合统计:")
        print("     - 曝光数、点击数、观看数")
        print("     - 观看时长、完播率")
        print("     - 互动数（点赞、分享、评论）")
        print("  4. 计算各项指标")
        print("  5. 推送到Prometheus Pushgateway")
        print("  6. 发送到recommendation-metrics Topic")
        print()
        print("🚀 启动命令:")
        print("  python flink_jobs/recommendation_metrics.py")
        print()


class MetricsAggregateFunction:
    """指标聚合函数"""
    
    @staticmethod
    def aggregate(behaviors: list[Dict[str, Any]]) -> Dict[str, Any]:
        """
        聚合计算推荐指标
        
        Args:
            behaviors: 窗口内的行为列表
            
        Returns:
            指标数据
        """
        if not behaviors:
            return {}
        
        # 基本信息
        first_behavior = behaviors[0]
        tenant_id = first_behavior['tenant_id']
        scenario_id = first_behavior['scenario_id']
        
        # 统计计数
        impression_count = 0
        click_count = 0
        view_count = 0
        complete_view_count = 0
        like_count = 0
        share_count = 0
        comment_count = 0
        
        # 观看时长统计
        total_watch_duration = 0
        
        for behavior in behaviors:
            action = behavior['action_type']
            extra = behavior.get('extra', {})
            
            if action == 'impression':
                impression_count += 1
            elif action == 'click':
                click_count += 1
            elif action == 'view':
                view_count += 1
                # 观看时长
                watch_duration = extra.get('watch_duration', 0)
                total_watch_duration += watch_duration
                # 完播
                if extra.get('completion_rate', 0) >= 0.9:
                    complete_view_count += 1
            elif action == 'like':
                like_count += 1
            elif action == 'share':
                share_count += 1
            elif action == 'comment':
                comment_count += 1
        
        # 计算指标
        ctr = click_count / impression_count if impression_count > 0 else 0
        avg_watch_duration = total_watch_duration / view_count if view_count > 0 else 0
        completion_rate = complete_view_count / view_count if view_count > 0 else 0
        engagement_rate = (like_count + share_count + comment_count) / impression_count \
                         if impression_count > 0 else 0
        
        return {
            'tenant_id': tenant_id,
            'scenario_id': scenario_id,
            'window_end': datetime.utcnow().isoformat(),
            'counts': {
                'impression': impression_count,
                'click': click_count,
                'view': view_count,
                'like': like_count,
                'share': share_count,
                'comment': comment_count
            },
            'metrics': {
                'ctr': round(ctr, 4),
                'avg_watch_duration': round(avg_watch_duration, 2),
                'completion_rate': round(completion_rate, 4),
                'engagement_rate': round(engagement_rate, 4)
            }
        }


if __name__ == '__main__':
    # 配置
    kafka_servers = 'localhost:9092'
    prometheus_pushgateway = 'localhost:9091'
    
    # 运行作业
    metrics = RecommendationMetrics(kafka_servers, prometheus_pushgateway)
    metrics.run()

