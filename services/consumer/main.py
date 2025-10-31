"""
Kafka Consumer 服务启动入口
"""
import sys
import asyncio
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.item.kafka_consumer import run_item_kafka_consumer


def main():
    """启动 Kafka Consumer"""
    print("=" * 70)
    print("🚀 启动 Kafka Consumer...")
    print("=" * 70)
    print(f"环境: {os.getenv('ENV', 'local')}")
    print(f"进程ID: {os.getpid()}")
    print("=" * 70)
    
    try:
        asyncio.run(run_item_kafka_consumer())
    except KeyboardInterrupt:
        print("\n\n收到中断信号，正在停止...")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n守护进程已退出")


if __name__ == "__main__":
    main()

