#!/usr/bin/env python3
"""
测试 Kafka 连接脚本
"""
import asyncio
import sys

async def test_kafka_connection():
    """测试 Kafka 连接"""
    kafka_server = "111.228.39.41:9092"
    
    print("=" * 70)
    print("Kafka 连接测试")
    print("=" * 70)
    print(f"测试服务器: {kafka_server}")
    print()
    
    # 测试 1: 基础网络连接
    print("📡 测试 1: 网络连通性")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(("111.228.39.41", 9092))
        sock.close()
        
        if result == 0:
            print(f"✅ TCP 端口 9092 可访问")
        else:
            print(f"❌ TCP 端口 9092 不可访问 (错误码: {result})")
            return
    except Exception as e:
        print(f"❌ 网络连接失败: {e}")
        return
    
    print()
    
    # 测试 2: aiokafka 库检查
    print("📦 测试 2: aiokafka 库检查")
    try:
        import aiokafka
        print(f"✅ aiokafka 已安装: {aiokafka.__version__}")
    except ImportError:
        print("❌ aiokafka 未安装，请运行: pip install aiokafka")
        return
    
    print()
    
    # 测试 3: Kafka Producer 连接
    print("🔌 测试 3: Kafka Producer 连接")
    try:
        from aiokafka import AIOKafkaProducer
        
        producer = AIOKafkaProducer(
            bootstrap_servers=kafka_server,
            request_timeout_ms=30000,
            metadata_max_age_ms=60000,
            connections_max_idle_ms=540000
        )
        
        print(f"正在连接 Kafka: {kafka_server}...")
        await producer.start()
        print(f"✅ Kafka Producer 连接成功！")
        
        # 获取 cluster metadata（简化版本）
        print(f"✅ Kafka 集群信息:")
        print(f"   - 连接状态: 已建立")
        print(f"   - Bootstrap Servers: {kafka_server}")
        
        await producer.stop()
        print(f"✅ Kafka Producer 已断开")
        
    except Exception as e:
        print(f"❌ Kafka Producer 连接失败:")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {e}")
        print()
        print("💡 可能的原因:")
        print("   1. Kafka 服务未启动")
        print("   2. KAFKA_ADVERTISED_LISTENERS 配置错误")
        print("   3. 防火墙阻止了 9092 端口")
        print("   4. Kafka 还在启动中（需要等待几秒）")
        return
    
    print()
    
    # 测试 4: Kafka Consumer 连接
    print("🔌 测试 4: Kafka Consumer 连接")
    try:
        from aiokafka import AIOKafkaConsumer
        
        consumer = AIOKafkaConsumer(
            bootstrap_servers=kafka_server,
            group_id="test-group",
            request_timeout_ms=30000
        )
        
        print(f"正在连接 Kafka Consumer...")
        await consumer.start()
        print(f"✅ Kafka Consumer 连接成功！")
        
        # 获取所有 topics
        topics = await consumer.topics()
        print(f"✅ 可用的 Topics: {topics if topics else '(无)'}")
        
        await consumer.stop()
        print(f"✅ Kafka Consumer 已断开")
        
    except Exception as e:
        print(f"❌ Kafka Consumer 连接失败:")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {e}")
    
    print()
    print("=" * 70)
    print("✅ Kafka 连接测试完成")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(test_kafka_connection())
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        sys.exit(1)

