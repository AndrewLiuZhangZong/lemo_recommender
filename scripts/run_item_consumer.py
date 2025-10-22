#!/usr/bin/env python
"""
物品Kafka消费者守护进程

启动方式:
    poetry run python scripts/run_item_consumer.py

或后台运行:
    nohup poetry run python scripts/run_item_consumer.py > logs/item_consumer.log 2>&1 &
"""
import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.item.kafka_consumer import run_item_kafka_consumer


def main():
    """主函数"""
    print("=" * 60)
    print(" 推荐系统 - 物品Kafka消费者守护进程")
    print("=" * 60)
    print(f"环境: {os.getenv('ENV', 'local')}")
    print(f"进程ID: {os.getpid()}")
    print("-" * 60)
    
    try:
        asyncio.run(run_item_kafka_consumer())
    except KeyboardInterrupt:
        print("\n\n收到中断信号，正在停止...")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        sys.exit(1)
    
    print("\n守护进程已退出")


if __name__ == "__main__":
    main()

