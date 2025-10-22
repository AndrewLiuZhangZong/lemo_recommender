"""
Flink Job 3: 实时指标统计
功能：从Kafka消费用户行为数据，实时计算推荐效果指标，输出到Prometheus
"""
import json
import sys
from datetime import datetime
from collections import defaultdict

try:
    from pyflink.datastream import StreamExecutionEnvironment
    from pyflink.datastream.window import TumblingProcessingTimeWindows
    from pyflink.common import Time, WatermarkStrategy
    from pyflink.datastream.functions import ProcessWindowFunction
    from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
    from pyflink.common.serialization import SimpleStringSchema
    PYFLINK_AVAILABLE = True
except ImportError:
    PYFLINK_AVAILABLE = False
    print("⚠️  PyFlink未安装，使用模拟模式")


class MetricsAggregator(ProcessWindowFunction):
    """指标聚合函数"""
    
    def process(self, key, context, elements):
        """
        聚合窗口内的行为数据，计算推荐效果指标
        
        Args:
            key: (tenant_id, scenario_id)
            context: 窗口上下文
            elements: 窗口内的所有行为
        """
        tenant_id, scenario_id = key
        
        # 统计计数器
        stats = {
            'total_views': 0,
            'total_clicks': 0,
            'total_likes': 0,
            'total_shares': 0,
            'total_comments': 0,
            'total_duration': 0,
            'finished_views': 0,
            'unique_users': set(),
            'unique_items': set()
        }
        
        for behavior in elements:
            action_type = behavior.get('action_type')
            
            # 基础计数
            if action_type == 'view':
                stats['total_views'] += 1
            elif action_type == 'click':
                stats['total_clicks'] += 1
            elif action_type == 'like':
                stats['total_likes'] += 1
            elif action_type == 'share':
                stats['total_shares'] += 1
            elif action_type == 'comment':
                stats['total_comments'] += 1
            
            # 观看时长统计
            extra = behavior.get('extra', {})
            if 'duration' in extra:
                try:
                    duration = float(extra['duration'])
                    stats['total_duration'] += duration
                    
                    # 判断是否完播（假设>80%为完播）
                    if 'video_duration' in extra:
                        video_duration = float(extra['video_duration'])
                        if video_duration > 0 and duration / video_duration > 0.8:
                            stats['finished_views'] += 1
                except:
                    pass
            
            # 去重统计
            stats['unique_users'].add(behavior.get('user_id'))
            stats['unique_items'].add(behavior.get('item_id'))
        
        # 计算指标
        total_views = stats['total_views']
        total_clicks = stats['total_clicks']
        
        metrics = {
            'tenant_id': tenant_id,
            'scenario_id': scenario_id,
            'window_start': context.window().start,
            'window_end': context.window().end,
            'metrics': {
                # 点击率
                'ctr': round(total_clicks / total_views, 4) if total_views > 0 else 0,
                
                # 平均观看时长（秒）
                'avg_watch_duration': round(stats['total_duration'] / total_views, 2) if total_views > 0 else 0,
                
                # 完播率
                'completion_rate': round(stats['finished_views'] / total_views, 4) if total_views > 0 else 0,
                
                # 互动率（点赞+分享+评论）
                'engagement_rate': round(
                    (stats['total_likes'] + stats['total_shares'] + stats['total_comments']) / total_views, 4
                ) if total_views > 0 else 0,
                
                # 活跃用户数
                'active_users': len(stats['unique_users']),
                
                # 曝光物品数
                'exposed_items': len(stats['unique_items']),
                
                # 总行为数
                'total_actions': total_views + total_clicks + stats['total_likes'] + stats['total_shares']
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        yield json.dumps(metrics, ensure_ascii=False)


class RecommendationMetrics:
    """推荐效果实时指标统计"""
    
    def __init__(
        self,
        kafka_servers: str = "localhost:9092",
        prometheus_pushgateway: str = "localhost:9091"
    ):
        self.kafka_servers = kafka_servers
        self.prometheus_pushgateway = prometheus_pushgateway
    
    def run(self):
        """运行Flink作业"""
        
        if not PYFLINK_AVAILABLE:
            print("=" * 60)
            print("  Flink Job: 推荐指标实时统计 (模拟模式)")
            print("=" * 60)
            print()
            print("📊 作业配置:")
            print(f"  - Kafka: {self.kafka_servers}")
            print(f"  - Prometheus: {self.prometheus_pushgateway}")
            print()
            print("⚠️  请安装PyFlink:")
            print("  pip install apache-flink")
            print()
            return
        
        print("=" * 60)
        print("  Flink Job: 推荐指标实时统计")
        print("=" * 60)
        
        # 1. 创建执行环境
        env = StreamExecutionEnvironment.get_execution_environment()
        env.set_parallelism(4)
        
        # 2. 从Kafka读取用户行为数据
        kafka_source = KafkaSource.builder() \
            .set_bootstrap_servers(self.kafka_servers) \
            .set_topics("user-behaviors-.*") \
            .set_group_id("recommendation-metrics") \
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
        
        # 4. 按场景分组，1分钟窗口聚合
        metrics = (
            parsed_behaviors
            .key_by(lambda x: (x['tenant_id'], x['scenario_id']))
            .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
            .process(MetricsAggregator())
        )
        
        # 5. 推送到Prometheus Pushgateway
        def push_to_prometheus(metrics_json):
            """推送指标到Prometheus"""
            try:
                import requests
                metrics_data = json.loads(metrics_json)
                
                tenant_id = metrics_data['tenant_id']
                scenario_id = metrics_data['scenario_id']
                m = metrics_data['metrics']
                
                # 构造Prometheus格式的指标
                prometheus_metrics = f"""
# TYPE recommendation_ctr gauge
recommendation_ctr{{tenant_id="{tenant_id}",scenario_id="{scenario_id}"}} {m['ctr']}

# TYPE recommendation_avg_duration gauge
recommendation_avg_duration{{tenant_id="{tenant_id}",scenario_id="{scenario_id}"}} {m['avg_watch_duration']}

# TYPE recommendation_completion_rate gauge
recommendation_completion_rate{{tenant_id="{tenant_id}",scenario_id="{scenario_id}"}} {m['completion_rate']}

# TYPE recommendation_engagement_rate gauge
recommendation_engagement_rate{{tenant_id="{tenant_id}",scenario_id="{scenario_id}"}} {m['engagement_rate']}

# TYPE recommendation_active_users gauge
recommendation_active_users{{tenant_id="{tenant_id}",scenario_id="{scenario_id}"}} {m['active_users']}

# TYPE recommendation_exposed_items gauge
recommendation_exposed_items{{tenant_id="{tenant_id}",scenario_id="{scenario_id}"}} {m['exposed_items']}
                """
                
                # 推送到Pushgateway
                url = f"http://{self.prometheus_pushgateway}/metrics/job/recommendation_metrics/instance/{tenant_id}_{scenario_id}"
                response = requests.post(url, data=prometheus_metrics)
                
                if response.status_code == 200:
                    print(f"[Prometheus] 推送成功: {tenant_id}/{scenario_id}")
                else:
                    print(f"[Prometheus] 推送失败: {response.status_code}")
                
            except Exception as e:
                print(f"[Prometheus] 推送失败: {e}")
        
        metrics.map(push_to_prometheus)
        
        # 6. 写入Kafka（供其他系统消费）
        def send_to_kafka(metrics_json):
            """发送到Kafka topic"""
            try:
                # 这里可以使用Kafka Producer发送到 recommendation-metrics topic
                print(f"[Kafka] 发送指标: {metrics_json[:100]}...")
            except Exception as e:
                print(f"[Kafka] 发送失败: {e}")
        
        metrics.map(send_to_kafka)
        
        # 7. 打印到控制台（调试用）
        metrics.print()
        
        # 8. 执行作业
        print("\n🚀 启动Flink作业...")
        env.execute("Recommendation Metrics Real-time")


def main():
    """主函数"""
    import os
    
    kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    prometheus_pushgateway = os.getenv('PROMETHEUS_PUSHGATEWAY', 'localhost:9091')
    
    metrics = RecommendationMetrics(
        kafka_servers=kafka_servers,
        prometheus_pushgateway=prometheus_pushgateway
    )
    
    try:
        metrics.run()
    except KeyboardInterrupt:
        print("\n\n收到中断信号，停止作业...")
    except Exception as e:
        print(f"\n\n❌ 作业失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
