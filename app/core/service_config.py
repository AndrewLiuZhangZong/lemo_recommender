"""
微服务统一配置管理

所有配置从环境变量加载，支持K8s ConfigMap
"""
import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceConfig(BaseSettings):
    """微服务通用配置"""
    
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )
    
    # ========== 服务基础配置 ==========
    service_name: str = Field(default="lemo-service")
    service_version: str = Field(default="2.0.0")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080)
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    
    # ========== MongoDB配置 ==========
    mongodb_url: str = Field(default="mongodb://localhost:27017")
    mongodb_database: str = Field(default="lemo_recommender")
    mongodb_min_pool_size: int = Field(default=10)
    mongodb_max_pool_size: int = Field(default=100)
    
    # ========== Redis配置 ==========
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_max_connections: int = Field(default=50)
    redis_ttl_l1: int = Field(default=300, description="L1缓存TTL（推荐结果，秒）")
    redis_ttl_l2: int = Field(default=3600, description="L2缓存TTL（热数据，秒）")
    redis_ttl_l3: int = Field(default=86400, description="L3缓存TTL（物品详情，秒）")
    
    # ========== Kafka配置 ==========
    kafka_bootstrap_servers: str = Field(default="localhost:9092")
    kafka_consumer_group: str = Field(default="lemo-recommender-group")
    kafka_behavior_topic: str = Field(default="user-behaviors", description="用户行为Topic")
    kafka_item_topic: str = Field(default="items-ingest", description="物品接入Topic")
    
    # ========== Milvus配置 ==========
    milvus_host: str = Field(default="localhost")
    milvus_port: int = Field(default=19530)
    milvus_enabled: bool = Field(default=False)
    
    # ========== 微服务URL配置 ==========
    recall_service_url: str = Field(default="localhost:8081", description="召回服务地址")
    ranking_service_url: str = Field(default="localhost:8082", description="精排服务地址")
    reranking_service_url: str = Field(default="localhost:8083", description="重排服务地址")
    user_service_url: str = Field(default="localhost:8084", description="用户服务地址")
    item_service_url: str = Field(default="localhost:8085", description="物品服务地址")
    behavior_service_url: str = Field(default="localhost:8086", description="行为服务地址")
    
    # ========== 推荐配置 ==========
    default_recommend_count: int = Field(default=20, description="默认推荐数量")
    max_recommend_count: int = Field(default=100, description="最大推荐数量")
    recall_timeout_seconds: float = Field(default=1.0, description="召回超时时间（秒）")
    rank_timeout_seconds: float = Field(default=0.5, description="精排超时时间（秒）")
    rerank_timeout_seconds: float = Field(default=0.3, description="重排超时时间（秒）")
    
    # ========== 召回策略配置（可后台配置覆盖） ==========
    recall_strategies: str = Field(
        default='[{"name":"als_cf","weight":0.5,"limit":200},{"name":"hot_items","weight":0.3,"limit":100},{"name":"user_cf","weight":0.2,"limit":100}]',
        description="召回策略配置（JSON字符串）"
    )
    
    # ========== 精排模型配置 ==========
    default_ranker: str = Field(default="deepfm", description="默认排序器：deepfm, simple_score, random")
    deepfm_model_path: str = Field(default="/models/deepfm.onnx", description="DeepFM模型路径")
    
    # ========== 特征工程配置 ==========
    feature_cache_enabled: bool = Field(default=True, description="是否启用特征缓存")
    feature_cache_ttl: int = Field(default=600, description="特征缓存TTL（秒）")
    
    # ========== 监控配置 ==========
    enable_metrics: bool = Field(default=True, description="是否启用Prometheus指标")
    metrics_port: int = Field(default=9000, description="Prometheus指标端口")
    
    # ========== 限流配置 ==========
    rate_limit_enabled: bool = Field(default=True, description="是否启用限流")
    rate_limit_requests_per_second: int = Field(default=100, description="每秒请求限制")
    
    # ========== Flink配置（实时计算服务专用） ==========
    flink_rest_url: str = Field(default="http://localhost:8081", description="Flink REST API地址")
    flink_operator_namespace: str = Field(default="lemo-dev", description="Flink Operator命名空间")
    
    # ========== Celery配置（Worker服务专用） ==========
    celery_broker_url: str = Field(default="redis://localhost:6379/1", description="Celery Broker")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", description="Celery Result Backend")


# 创建全局配置实例
service_config = ServiceConfig()


def get_service_config() -> ServiceConfig:
    """获取服务配置"""
    return service_config

