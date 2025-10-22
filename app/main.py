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
    print("🚀 启动推荐系统...")
    await mongodb.connect()
    await redis_client.connect()
    yield
    # 关闭时
    print("👋 关闭推荐系统...")
    await mongodb.close()
    await redis_client.close()


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
    from app.api.v1 import scenario, item, interaction, recommendation, admin, experiment, jobs, model_training, recall_config, model_management, feature_config
    
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
        tags=["行为采集"]
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

