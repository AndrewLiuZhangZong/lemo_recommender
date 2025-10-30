#!/usr/bin/env python3
"""
检查 Worker/Beat/Consumer 服务的依赖连接
"""
import sys


def check_redis():
    """检查 Redis 连接"""
    try:
        import redis
        r = redis.Redis.from_url("redis://:redis_password_2024@111.228.39.41:6379/1", 
                                  socket_connect_timeout=5)
        r.ping()
        print("✅ Redis 连接成功")
        return True
    except ImportError:
        print("❌ Redis 库未安装: pip install redis")
        return False
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        return False


def check_mongodb():
    """检查 MongoDB 连接"""
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://admin:password@111.228.39.41:27017",
                            serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("✅ MongoDB 连接成功")
        return True
    except ImportError:
        print("❌ PyMongo 库未安装: pip install pymongo")
        return False
    except Exception as e:
        print(f"❌ MongoDB 连接失败: {e}")
        return False


def check_kafka():
    """检查 Kafka 连接"""
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers="111.228.39.41:9092",
            request_timeout_ms=5000,
            api_version_auto_timeout_ms=5000
        )
        producer.close()
        print("✅ Kafka 连接成功")
        return True
    except ImportError:
        print("❌ Kafka 库未安装: pip install kafka-python")
        return False
    except Exception as e:
        print(f"❌ Kafka 连接失败: {e}")
        return False


def check_milvus():
    """检查 Milvus 连接（可选）"""
    try:
        from pymilvus import connections
        connections.connect(
            alias="default",
            host="111.228.39.41",
            port="19530",
            timeout=5
        )
        print("✅ Milvus 连接成功")
        connections.disconnect("default")
        return True
    except ImportError:
        print("⚠️  Milvus 库未安装（可选）: pip install pymilvus")
        return None  # 可选组件
    except Exception as e:
        print(f"⚠️  Milvus 连接失败（可选）: {e}")
        return None


def check_clickhouse():
    """检查 ClickHouse 连接（可选）"""
    try:
        from clickhouse_driver import Client
        client = Client(
            host="111.228.39.41",
            port=9900,  # 映射端口（避免与 MinIO 9000 冲突）
            user="default",
            password="clickhouse_2024",
            connect_timeout=5
        )
        client.execute("SELECT 1")
        print("✅ ClickHouse 连接成功")
        return True
    except ImportError:
        print("⚠️  ClickHouse 库未安装（可选）: pip install clickhouse-driver")
        return None
    except Exception as e:
        print(f"⚠️  ClickHouse 连接失败（可选，数据分析需要）: {e}")
        return None


def check_celery_libraries():
    """检查 Celery 相关库"""
    try:
        import celery
        print(f"✅ Celery 已安装: {celery.__version__}")
        
        try:
            import redbeat
            print(f"✅ celery-redbeat 已安装: {redbeat.__version__}")
        except ImportError:
            print("⚠️  celery-redbeat 未安装（Beat 服务推荐）: pip install celery-redbeat")
        
        return True
    except ImportError:
        print("❌ Celery 未安装: pip install celery[redis]")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("检查 Worker/Beat/Consumer 服务依赖")
    print("=" * 60)
    print()
    
    results = {
        "必需组件": {},
        "可选组件": {}
    }
    
    # 必需组件
    print("🔍 检查必需组件...")
    results["必需组件"]["Redis"] = check_redis()
    results["必需组件"]["MongoDB"] = check_mongodb()
    results["必需组件"]["Kafka"] = check_kafka()
    results["必需组件"]["Celery"] = check_celery_libraries()
    
    print()
    
    # 可选组件
    print("🔍 检查可选组件...")
    results["可选组件"]["Milvus"] = check_milvus()
    results["可选组件"]["ClickHouse"] = check_clickhouse()
    
    print()
    print("=" * 60)
    print("检查结果汇总")
    print("=" * 60)
    
    # 统计必需组件
    required_ok = sum(1 for v in results["必需组件"].values() if v is True)
    required_total = len(results["必需组件"])
    
    print(f"\n📊 必需组件: {required_ok}/{required_total} 通过")
    for name, status in results["必需组件"].items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}")
    
    # 统计可选组件
    optional_ok = sum(1 for v in results["可选组件"].values() if v is True)
    optional_total = len([v for v in results["可选组件"].values() if v is not None])
    
    print(f"\n📊 可选组件: {optional_ok}/{len(results['可选组件'])} 可用")
    for name, status in results["可选组件"].items():
        if status is True:
            icon = "✅"
        elif status is None:
            icon = "⚠️ "
        else:
            icon = "❌"
        print(f"  {icon} {name}")
    
    # 判断是否可以运行
    print()
    if required_ok == required_total:
        print("✅ 所有必需组件连接正常，可以启动 Worker/Beat/Consumer 服务！")
        return 0
    else:
        print("❌ 部分必需组件连接失败，请先修复后再启动服务。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

