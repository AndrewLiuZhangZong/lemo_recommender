"""gRPC 服务器主程序"""
import sys
import asyncio
import logging
from concurrent import futures
from pathlib import Path

# 添加 grpc_generated 到 Python 路径
grpc_gen_path = Path(__file__).parent.parent / "grpc_generated" / "python"
sys.path.insert(0, str(grpc_gen_path))

import grpc
from recommender.v1 import (
    scenario_pb2_grpc,
    item_pb2_grpc,
    experiment_pb2_grpc,
    analytics_pb2_grpc,
    model_pb2_grpc,
    template_pb2_grpc,
    dataset_pb2_grpc,
    behavior_pb2_grpc,
)

from .services import (
    ScenarioServicer,
    ItemServicer,
    ExperimentServicer,
    AnalyticsServicer,
    ModelServicer,
    TemplateServicer,
    DatasetServicer,
    BehaviorServicer,
)

# 导入数据库和配置
from app.core.database import mongodb, redis_client
from app.core.config import settings
from app.core.kafka import init_kafka_producer, startup_kafka

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def serve(host: str = "0.0.0.0", port: int = 50051):
    """启动 gRPC 服务器"""
    
    logger.info("=" * 70)
    logger.info("🚀 启动 gRPC 服务器...")
    logger.info("=" * 70)
    logger.info("📝 配置信息:")
    logger.info(f"   应用: {settings.app_name} v{settings.app_version}")
    logger.info(f"   MongoDB: {settings.mongodb_url}")
    logger.info(f"   Redis: {settings.redis_url}")
    logger.info(f"   Kafka: {settings.kafka_bootstrap_servers}")
    logger.info(f"   gRPC 地址: {host}:{port}")
    logger.info("=" * 70)
    
    # 初始化数据库连接
    logger.info("🔌 连接外部服务...")
    await mongodb.connect()
    db = mongodb.get_database()
    logger.info("  ✓ MongoDB 连接成功")
    
    # 初始化 Redis 连接
    await redis_client.connect()
    
    # 初始化 Kafka Producer
    if settings.kafka_bootstrap_servers:
        try:
            init_kafka_producer(settings.kafka_bootstrap_servers)
            await startup_kafka()
            logger.info("  ✓ Kafka Producer 已启动")
        except Exception as e:
            logger.warning(f"  ⚠️  Kafka Producer 启动失败（降级模式）: {e}")
    
    # 创建服务器
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
            ('grpc.max_send_message_length', 100 * 1024 * 1024),     # 100MB
        ]
    )
    
    # 注册服务
    logger.info("注册 gRPC 服务...")
    
    scenario_pb2_grpc.add_ScenarioServiceServicer_to_server(
        ScenarioServicer(db), server
    )
    logger.info("  ✓ ScenarioService")
    
    item_pb2_grpc.add_ItemServiceServicer_to_server(
        ItemServicer(db), server
    )
    logger.info("  ✓ ItemService")
    
    experiment_pb2_grpc.add_ExperimentServiceServicer_to_server(
        ExperimentServicer(db), server
    )
    logger.info("  ✓ ExperimentService")
    
    analytics_pb2_grpc.add_AnalyticsServiceServicer_to_server(
        AnalyticsServicer(db), server
    )
    logger.info("  ✓ AnalyticsService")
    
    model_pb2_grpc.add_ModelServiceServicer_to_server(
        ModelServicer(db), server
    )
    logger.info("  ✓ ModelService")
    
    template_pb2_grpc.add_TemplateServiceServicer_to_server(
        TemplateServicer(db), server
    )
    logger.info("  ✓ TemplateService")
    
    dataset_pb2_grpc.add_DatasetServiceServicer_to_server(
        DatasetServicer(db), server
    )
    logger.info("  ✓ DatasetService")
    
    # ⭐ v2.0架构：BehaviorService（不需要db，直接发送到Kafka）
    behavior_pb2_grpc.add_BehaviorServiceServicer_to_server(
        BehaviorServicer(), server
    )
    logger.info("  ✓ BehaviorService (v2.0 - Kafka)")
    
    # 绑定端口
    listen_addr = f'{host}:{port}'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"🚀 gRPC 服务器启动在 {listen_addr}")
    logger.info("="*60)
    logger.info("可用服务:")
    logger.info("  - lemo.recommender.v1.ScenarioService")
    logger.info("  - lemo.recommender.v1.ItemService")
    logger.info("  - lemo.recommender.v1.ExperimentService")
    logger.info("  - lemo.recommender.v1.AnalyticsService")
    logger.info("  - lemo.recommender.v1.ModelService")
    logger.info("  - lemo.recommender.v1.TemplateService")
    logger.info("  - lemo.recommender.v1.DatasetService")
    logger.info("  - lemo.recommender.v1.BehaviorService ⭐ v2.0")
    logger.info("="*60)
    
    # 启动服务器
    await server.start()
    
    # 等待终止
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("\n⏹️  正在关闭 gRPC 服务器...")
        await server.stop(grace=5)
        await mongodb.disconnect()
        logger.info("✅ gRPC 服务器已关闭")
def main():
    """主函数"""
    import os
    
    # 从环境变量读取配置
    host = os.getenv("GRPC_HOST", "0.0.0.0")
    port = int(os.getenv("GRPC_PORT", "50051"))
    
    # 运行服务器
    try:
        asyncio.run(serve(host, port))
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

