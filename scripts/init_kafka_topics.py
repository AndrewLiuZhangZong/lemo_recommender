#!/usr/bin/env python3
"""
初始化 Kafka Topics
创建推荐系统所需的所有 Topic
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from app.core.config import settings


def init_kafka_topics():
    """初始化 Kafka Topics"""
    print("=" * 70)
    print("初始化 Kafka Topics".center(66))
    print("=" * 70)
    
    kafka_server = settings.kafka_bootstrap_servers
    topics = settings.kafka_item_ingest_topics
    
    print(f"\n📡 Kafka 服务器: {kafka_server}")
    print(f"📋 待创建 Topics: {topics}")
    print()
    
    try:
        import asyncio
        from aiokafka import AIOKafkaClient
        from aiokafka.admin import AIOKafkaAdminClient, NewTopic
        from aiokafka.errors import TopicAlreadyExistsError
        
        async def create_topics():
            # 创建 Admin Client
            print(f"🔌 连接 Kafka Admin...")
            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=kafka_server,
                client_id='kafka-topic-initializer'
            )
            
            try:
                await admin_client.start()
                print(f"✅ 已连接 Kafka\n")
                
                # 获取现有 Topics（通过创建一个临时的 client）
                client = AIOKafkaClient(bootstrap_servers=kafka_server)
                await client.bootstrap()
                cluster = client.cluster
                existing_topics = cluster.topics()
                await client.close()
                
                print(f"📋 现有 Topics: {existing_topics}\n")
                
                # 创建 Topics
                topics_to_create = []
                for topic_name in topics:
                    if topic_name not in existing_topics:
                        topics_to_create.append(
                            NewTopic(
                                name=topic_name,
                                num_partitions=3,  # 3个分区，提高并发
                                replication_factor=1  # 单节点，副本数为1
                            )
                        )
                        print(f"📝 准备创建: {topic_name} (3 partitions, 1 replica)")
                    else:
                        print(f"✓ Topic 已存在: {topic_name}")
                
                if topics_to_create:
                    print(f"\n🚀 创建 {len(topics_to_create)} 个 Topics...")
                    try:
                        await admin_client.create_topics(topics_to_create)
                        for topic in topics_to_create:
                            print(f"✅ 成功创建: {topic.name}")
                    except TopicAlreadyExistsError as e:
                        print(f"⚠️  某些 Topic 已存在: {e}")
                    except Exception as e:
                        print(f"❌ 创建失败: {e}")
                        return False
                else:
                    print("\n✅ 所有 Topics 已存在，无需创建")
                
                # 验证创建结果
                print("\n🔍 验证 Topics...")
                client = AIOKafkaClient(bootstrap_servers=kafka_server)
                await client.bootstrap()
                cluster = client.cluster
                all_topics = cluster.topics()
                await client.close()
                
                print("\n📋 最终 Topics 列表:")
                for topic in sorted(all_topics):
                    if not topic.startswith('__'):  # 跳过内部 topics
                        print(f"  - {topic}")
                
                return True
                
            finally:
                await admin_client.close()
        
        # 运行异步函数
        result = asyncio.run(create_topics())
        
        if result:
            print("\n" + "=" * 70)
            print("✅ Kafka Topics 初始化完成".center(66))
            print("=" * 70)
        
        return result
        
    except ImportError:
        print("❌ aiokafka 未安装")
        print("   请运行: pip install aiokafka")
        return False
    except Exception as e:
        print(f"❌ Kafka 连接或操作失败: {e}")
        print(f"\n💡 可能的原因:")
        print(f"   1. Kafka 服务未启动")
        print(f"   2. Kafka 地址配置错误: {kafka_server}")
        print(f"   3. 防火墙阻止了 9092 端口")
        return False


if __name__ == '__main__':
    success = init_kafka_topics()
    sys.exit(0 if success else 1)

