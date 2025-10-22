"""
应用配置管理
使用 pydantic-settings 管理配置，支持环境变量
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用配置
    app_name: str = "Lemo Recommender"
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # MongoDB配置
    mongodb_url: str = Field(default="mongodb://admin:password@localhost:27017")
    mongodb_database: str = "lemo_recommender"
    mongodb_min_pool_size: int = 10
    mongodb_max_pool_size: int = 100
    
    # Redis配置
    redis_url: str = Field(default="redis://:redis_password@localhost:6379/0")
    redis_max_connections: int = 50
    
    # Kafka配置
    kafka_bootstrap_servers: str = Field(default="localhost:9092")
    kafka_consumer_group: str = "lemo-recommender-group"
    
    # Kafka消费者Topic配置
    kafka_item_ingest_topics: List[str] = Field(default=["items-ingest", "vlog-items", "news-items"])
    
    # 外部服务配置
    tenant_service_grpc_url: str = Field(default="localhost:9000")
    user_service_grpc_url: str = Field(default="localhost:9001")
    
    # 缓存配置
    cache_ttl_tenant_config: int = 3600  # 1小时
    cache_ttl_user_info: int = 1800  # 30分钟
    cache_ttl_scenario_config: int = 3600  # 1小时
    cache_ttl_recommend_result: int = 600  # 10分钟
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    
    # 监控配置
    enable_metrics: bool = True
    metrics_port: int = 9000
    
    # 安全配置
    secret_key: str = Field(default="your-secret-key-change-in-production")
    access_token_expire_minutes: int = 30
    
    # 推荐系统配置
    default_recommend_count: int = 20
    max_recommend_count: int = 100
    recall_timeout_seconds: float = 1.0
    rank_timeout_seconds: float = 0.5
    
    # 向量检索配置（第二阶段，使用本地已有Milvus服务）
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_http_port: int = 9091
    milvus_enabled: bool = False
    
    # Celery配置
    celery_broker_url: str = Field(default="redis://:redis_password@localhost:6379/1")
    celery_result_backend: str = Field(default="redis://:redis_password@localhost:6379/2")
    celery_enabled: bool = True  # 是否启用Celery异步任务
    
    @field_validator("kafka_item_ingest_topics", mode="before")
    @classmethod
    def parse_kafka_topics(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",")]
        return v


# 全局配置实例
settings = Settings()

