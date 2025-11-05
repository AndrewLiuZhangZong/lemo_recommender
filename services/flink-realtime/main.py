# -*- coding: utf-8 -*-
"""
Flink实时特征服务
职责：实时计算用户特征、物品特征、窗口统计
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
from app.core.service_config import ServiceConfig

def create_flink_job():
    """创建Flink实时特征计算任务"""
    
    # 创建执行环境
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(4)
    
    # 创建Table环境
    settings = EnvironmentSettings.new_instance() \
        .in_streaming_mode() \
        .build()
    table_env = StreamTableEnvironment.create(env, environment_settings=settings)
    
    # 配置
    config = ServiceConfig()
    kafka_servers = config.kafka_bootstrap_servers
    
    # 创建Kafka Source表（用户行为）
    table_env.execute_sql(f"""
        CREATE TABLE user_behaviors (
            tenant_id STRING,
            scenario_id STRING,
            user_id STRING,
            item_id STRING,
            action_type STRING,
            timestamp BIGINT,
            event_time AS TO_TIMESTAMP(FROM_UNIXTIME(timestamp / 1000)),
            WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'user_behaviors',
            'properties.bootstrap.servers' = '{kafka_servers}',
            'properties.group.id' = 'flink-realtime-features',
            'scan.startup.mode' = 'latest-offset',
            'format' = 'json'
        )
    """)
    
    # 创建实时特征计算（1小时滑动窗口）
    table_env.execute_sql("""
        CREATE TABLE user_realtime_features (
            user_id STRING,
            tenant_id STRING,
            scenario_id STRING,
            recent_view_count BIGINT,
            recent_like_count BIGINT,
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            PRIMARY KEY (user_id, tenant_id, scenario_id) NOT ENFORCED
        ) WITH (
            'connector' = 'upsert-kafka',
            'topic' = 'user_realtime_features',
            'properties.bootstrap.servers' = '{kafka_servers}',
            'key.format' = 'json',
            'value.format' = 'json'
        )
    """.replace('{kafka_servers}', kafka_servers))
    
    # 实时特征计算SQL
    table_env.execute_sql("""
        INSERT INTO user_realtime_features
        SELECT 
            user_id,
            tenant_id,
            scenario_id,
            COUNT(CASE WHEN action_type = 'VIEW' THEN 1 END) as recent_view_count,
            COUNT(CASE WHEN action_type = 'LIKE' THEN 1 END) as recent_like_count,
            TUMBLE_START(event_time, INTERVAL '1' HOUR) as window_start,
            TUMBLE_END(event_time, INTERVAL '1' HOUR) as window_end
        FROM user_behaviors
        GROUP BY 
            user_id,
            tenant_id,
            scenario_id,
            TUMBLE(event_time, INTERVAL '1' HOUR)
    """)
    
    print("[FlinkRealtimeService] Flink任务已启动")


if __name__ == '__main__':
    try:
        create_flink_job()
    except Exception as e:
        print(f"[FlinkRealtimeService] Flink任务启动失败: {e}")
        import traceback
        traceback.print_exc()
