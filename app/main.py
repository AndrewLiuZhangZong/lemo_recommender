"""
FastAPI应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import mongodb, redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("=" * 70)
    print("🚀 启动推荐系统...")
    print("=" * 70)
    print(f"📝 配置信息:")
    print(f"   应用: {settings.app_name} v{settings.app_version}")
    print(f"   调试模式: {'开启' if settings.debug else '关闭'}")
    print(f"   MongoDB URL: {settings.mongodb_url}")
    print(f"   MongoDB DB: {settings.mongodb_database}")
    print(f"   Redis URL: {settings.redis_url}")
    print(f"   Kafka Bootstrap: {settings.kafka_bootstrap_servers}")
    print(f"   Kafka Topics (Item Ingest): {settings.kafka_item_ingest_topics}")
    print(f"   Milvus: {settings.milvus_host}:{settings.milvus_port}")
    print(f"   Celery Broker: {settings.celery_broker_url}")
    print(f"   Celery Backend: {settings.celery_result_backend}")
    print("=" * 70)
    
    # 初始化数据库连接
    print("🔌 连接外部服务...")
    await mongodb.connect()
    await redis_client.connect()
    
    # 初始化Kafka Producer（v2.0架构 - behavior服务需要）
    from app.core.kafka import init_kafka_producer, startup_kafka
    if settings.kafka_bootstrap_servers:
        try:
            init_kafka_producer(settings.kafka_bootstrap_servers)
            await startup_kafka()
            print("✅ Kafka Producer已启动")
        except Exception as e:
            print(f"⚠️  Kafka Producer启动失败（降级模式）: {e}")
    else:
        print("⚠️  Kafka未配置，behavior服务将以降级模式运行")
    
    print("=" * 70)
    print("✅ 推荐系统启动完成！")
    print("=" * 70)
    
    yield
    
    # 关闭时
    print("=" * 70)
    print("👋 关闭推荐系统...")
    print("=" * 70)
    
    # 关闭Kafka Producer
    from app.core.kafka import shutdown_kafka
    try:
        await shutdown_kafka()
        print("✅ Kafka Producer已关闭")
    except Exception as e:
        print(f"⚠️  Kafka Producer关闭失败: {e}")
    
    await mongodb.close()
    await redis_client.close()
    
    print("=" * 70)
    print("✅ 推荐系统已关闭")
    print("=" * 70)


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="多场景SaaS推荐系统",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    from app.api.v1 import (
        scenario, item, interaction, recommendation, admin, 
        experiment, jobs, model_training, recall_config, 
        model_management, feature_config, behavior, scenario_tracking
    )
    
    app.include_router(
        scenario.router,
        prefix=f"{settings.api_prefix}/scenarios",
        tags=["场景管理"]
    )
    
    app.include_router(
        item.router,
        prefix=f"{settings.api_prefix}/items",
        tags=["物品管理"]
    )
    
    app.include_router(
        interaction.router,
        prefix=f"{settings.api_prefix}/interactions",
        tags=["行为采集（旧版）"]
    )
    
    # ⭐ v2.0架构：新的行为采集服务
    app.include_router(
        behavior.router,
        prefix=f"{settings.api_prefix}",  # behavior router已包含/behaviors前缀
        tags=["行为采集v2"]
    )
    
    app.include_router(
        recommendation.router,
        prefix=f"{settings.api_prefix}/recommend",
        tags=["推荐服务"]
    )
    
    app.include_router(
        admin.router,
        prefix=f"{settings.api_prefix}/admin",
        tags=["管理后台"]
    )
    
    app.include_router(
        experiment.router,
        prefix=f"{settings.api_prefix}/experiments",
        tags=["AB实验"]
    )
    
    app.include_router(
        jobs.router,
        prefix=f"{settings.api_prefix}/jobs",
        tags=["作业管理"]
    )
    
    app.include_router(
        model_training.router,
        prefix=f"{settings.api_prefix}/model-training",
        tags=["模型训练"]
    )
    
    app.include_router(
        recall_config.router,
        prefix=f"{settings.api_prefix}/recall-config",
        tags=["召回配置"]
    )
    
    app.include_router(
        model_management.router,
        prefix=f"{settings.api_prefix}/model-management",
        tags=["模型管理"]
    )
    
    app.include_router(
        feature_config.router,
        prefix=f"{settings.api_prefix}/feature-config",
        tags=["实时特征配置"]
    )
    
    # ⭐ v2.0架构：场景埋点配置管理
    app.include_router(
        scenario_tracking.router,
        prefix=f"{settings.api_prefix}",  # scenario_tracking router已包含/tracking-configs前缀
        tags=["场景埋点配置"]
    )
    
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
        }
    
    @app.get("/health")
    async def health_check():
        """健康检查"""
        try:
            health_status = {"status": "healthy"}
            
            # 检查MongoDB
            await mongodb.client.admin.command('ping')
            health_status["mongodb"] = "ok"
            
            # 检查Redis（可选）
            if redis_client.client:
                await redis_client.client.ping()
                health_status["redis"] = "ok"
            else:
                health_status["redis"] = "disabled"
            
            return health_status
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "error": str(e)}
            )
    
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

