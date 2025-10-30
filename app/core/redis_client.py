"""
同步 Redis 客户端（用于 Celery 任务等同步场景）
"""
import redis
from typing import Optional
from app.core.config import settings


# 全局同步 Redis 客户端
_sync_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """
    获取同步 Redis 客户端（单例模式）
    
    用于 Celery 任务等同步场景
    对于异步场景，请使用 app.core.database.get_redis()
    
    Returns:
        redis.Redis: 同步 Redis 客户端
    """
    global _sync_redis_client
    
    if _sync_redis_client is None:
        # 解析 Redis URL
        redis_url = settings.redis_url
        
        # 创建同步 Redis 客户端
        _sync_redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30
        )
        
        # 测试连接
        try:
            _sync_redis_client.ping()
            print(f"✅ 同步 Redis 客户端连接成功")
        except Exception as e:
            print(f"⚠️  同步 Redis 客户端连接失败: {e}")
    
    return _sync_redis_client


def close_redis_client():
    """关闭 Redis 客户端连接"""
    global _sync_redis_client
    
    if _sync_redis_client is not None:
        _sync_redis_client.close()
        _sync_redis_client = None
        print("同步 Redis 客户端连接已关闭")

