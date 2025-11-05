#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一初始化脚本 - 初始化所有第三方组件
包括: MongoDB, ClickHouse, Kafka, Milvus
"""
import sys
import os
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pymongo import MongoClient
from clickhouse_driver import Client as ClickHouseClient
from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType
import redis


def init_mongodb(mongo_url: str = "mongodb://localhost:27017"):
    """初始化MongoDB"""
    print("\n" + "="*60)
    print("📦 初始化MongoDB...")
    print("="*60)
    
    try:
        client = MongoClient(mongo_url)
        db = client["lemo_recommender"]
        
        # 创建集合和索引
        collections = {
            "scenarios": [
                ("tenant_id", 1),
                ("scenario_id", 1),
                [("tenant_id", 1), ("scenario_id", 1)]
            ],
            "items": [
                ("tenant_id", 1),
                ("scenario_id", 1),
                ("item_id", 1),
                [("tenant_id", 1), ("scenario_id", 1), ("item_id", 1)]
            ],
            "user_profiles": [
                ("tenant_id", 1),
                ("scenario_id", 1),
                ("user_id", 1),
                [("tenant_id", 1), ("scenario_id", 1), ("user_id", 1)]
            ],
            "models": [
                ("tenant_id", 1),
                ("scenario_id", 1),
                ("model_name", 1),
                ("status", 1)
            ],
            "experiments": [
                ("tenant_id", 1),
                ("scenario_id", 1),
                ("experiment_id", 1),
                ("status", 1)
            ]
        }
        
        for coll_name, indexes in collections.items():
            if coll_name not in db.list_collection_names():
                db.create_collection(coll_name)
                print(f"✅ 创建集合: {coll_name}")
            
            coll = db[coll_name]
            for idx in indexes:
                if isinstance(idx, tuple):
                    coll.create_index([idx])
                else:
                    coll.create_index(idx)
            print(f"✅ 创建索引: {coll_name}")
        
        print("\n✅ MongoDB初始化完成")
        return True
        
    except Exception as e:
        print(f"\n❌ MongoDB初始化失败: {e}")
        return False


def init_clickhouse(host: str = "localhost", port: int = 8123):
    """初始化ClickHouse"""
    print("\n" + "="*60)
    print("📦 初始化ClickHouse...")
    print("="*60)
    
    try:
        client = ClickHouseClient(host=host, port=port)
        
        # 创建数据库
        client.execute("CREATE DATABASE IF NOT EXISTS lemo_recommender")
        print("✅ 创建数据库: lemo_recommender")
        
        # 创建用户行为表
        client.execute("""
            CREATE TABLE IF NOT EXISTS lemo_recommender.user_behaviors (
                tenant_id String,
                scenario_id String,
                user_id String,
                item_id String,
                action_type String,
                timestamp DateTime,
                event_id String,
                device_type String,
                context String,
                extra_data String,
                date Date DEFAULT toDate(timestamp)
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(date)
            ORDER BY (tenant_id, scenario_id, user_id, timestamp)
            TTL date + INTERVAL 90 DAY
            SETTINGS index_granularity = 8192
        """)
        print("✅ 创建表: user_behaviors")
        
        # 创建推荐日志表
        client.execute("""
            CREATE TABLE IF NOT EXISTS lemo_recommender.recommendation_logs (
                tenant_id String,
                scenario_id String,
                user_id String,
                request_id String,
                item_ids Array(String),
                timestamp DateTime,
                recall_count UInt32,
                rank_count UInt32,
                final_count UInt32,
                latency_ms UInt32,
                date Date DEFAULT toDate(timestamp)
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(date)
            ORDER BY (tenant_id, scenario_id, timestamp)
            TTL date + INTERVAL 30 DAY
            SETTINGS index_granularity = 8192
        """)
        print("✅ 创建表: recommendation_logs")
        
        print("\n✅ ClickHouse初始化完成")
        return True
        
    except Exception as e:
        print(f"\n❌ ClickHouse初始化失败: {e}")
        return False


def init_kafka(bootstrap_servers: str = "localhost:9092"):
    """初始化Kafka"""
    print("\n" + "="*60)
    print("📦 初始化Kafka...")
    print("="*60)
    
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            client_id='init_script'
        )
        
        # 创建Topics
        topics = [
            NewTopic(name="user_behaviors", num_partitions=6, replication_factor=1),
            NewTopic(name="recommendation_logs", num_partitions=3, replication_factor=1),
            NewTopic(name="user_realtime_features", num_partitions=3, replication_factor=1),
            NewTopic(name="realtime_recommendations", num_partitions=3, replication_factor=1),
        ]
        
        existing_topics = admin_client.list_topics()
        
        for topic in topics:
            if topic.name not in existing_topics:
                admin_client.create_topics([topic])
                print(f"✅ 创建Topic: {topic.name}")
            else:
                print(f"ℹ️  Topic已存在: {topic.name}")
        
        admin_client.close()
        print("\n✅ Kafka初始化完成")
        return True
        
    except Exception as e:
        print(f"\n❌ Kafka初始化失败: {e}")
        return False


def init_milvus(host: str = "localhost", port: int = 19530):
    """初始化Milvus"""
    print("\n" + "="*60)
    print("📦 初始化Milvus...")
    print("="*60)
    
    try:
        connections.connect(host=host, port=port)
        
        # 创建collection
        collection_name = "item_embeddings"
        
        # 检查是否已存在
        from pymilvus import utility
        if utility.has_collection(collection_name):
            print(f"ℹ️  Collection已存在: {collection_name}")
            connections.disconnect("default")
            print("\n✅ Milvus初始化完成")
            return True
        
        # 定义schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="scenario_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="item_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128)
        ]
        
        schema = CollectionSchema(fields=fields, description="Item embeddings")
        collection = Collection(name=collection_name, schema=schema)
        
        # 创建索引
        index_params = {
            "metric_type": "IP",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        
        print(f"✅ 创建Collection: {collection_name}")
        
        connections.disconnect("default")
        print("\n✅ Milvus初始化完成")
        return True
        
    except Exception as e:
        print(f"\n❌ Milvus初始化失败: {e}")
        return False


def init_redis(host: str = "localhost", port: int = 6379):
    """初始化Redis"""
    print("\n" + "="*60)
    print("📦 初始化Redis...")
    print("="*60)
    
    try:
        r = redis.Redis(host=host, port=port, db=0)
        r.ping()
        print("✅ Redis连接成功")
        
        # 测试写入
        r.set("lemo:init:test", "ok", ex=60)
        print("✅ Redis写入测试成功")
        
        print("\n✅ Redis初始化完成")
        return True
        
    except Exception as e:
        print(f"\n❌ Redis初始化失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 Lemo推荐系统 - 第三方组件初始化")
    print("="*60)
    
    # 从环境变量读取配置
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    clickhouse_host = os.getenv("CLICKHOUSE_HOST", "localhost")
    clickhouse_port = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    milvus_host = os.getenv("MILVUS_HOST", "localhost")
    milvus_port = int(os.getenv("MILVUS_PORT", "19530"))
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    
    results = {}
    
    # 初始化各组件
    results['MongoDB'] = init_mongodb(mongo_url)
    time.sleep(1)
    
    results['ClickHouse'] = init_clickhouse(clickhouse_host, clickhouse_port)
    time.sleep(1)
    
    results['Kafka'] = init_kafka(kafka_servers)
    time.sleep(1)
    
    results['Milvus'] = init_milvus(milvus_host, milvus_port)
    time.sleep(1)
    
    results['Redis'] = init_redis(redis_host, redis_port)
    
    # 打印总结
    print("\n" + "="*60)
    print("📊 初始化结果总结")
    print("="*60)
    
    for component, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{component}: {status}")
    
    all_success = all(results.values())
    
    if all_success:
        print("\n🎉 所有组件初始化成功！")
        return 0
    else:
        print("\n⚠️  部分组件初始化失败，请检查日志")
        return 1


if __name__ == "__main__":
    sys.exit(main())

