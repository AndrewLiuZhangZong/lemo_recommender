"""
数据库连接管理
"""
import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional

from app.core.config import settings


class MongoDB:
    """MongoDB连接管理"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """建立连接"""
        self.client = AsyncIOMotorClient(
            settings.mongodb_url,
            minPoolSize=settings.mongodb_min_pool_size,
            maxPoolSize=settings.mongodb_max_pool_size,
        )
        self.db = self.client[settings.mongodb_database]
        
        # 测试连接
        await self.client.admin.command('ping')
        print(f"✅ MongoDB连接成功: {settings.mongodb_database}")
    
    async def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()
            print("MongoDB连接已关闭")
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """获取数据库实例"""
        if self.db is None:
            raise RuntimeError("MongoDB未连接，请先调用connect()")
        return self.db
    
    def get_collection(self, name: str):
        """获取集合"""
        return self.get_database()[name]


class Redis:
    """Redis连接管理"""
    
    pool: Optional[aioredis.ConnectionPool] = None
    client: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """建立连接池"""
        self.pool = aioredis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
        )
        self.client = aioredis.Redis(connection_pool=self.pool)
        
        # 测试连接
        await self.client.ping()
        print(f"✅ Redis连接成功: {settings.redis_url.split('@')[-1]}")
    
    async def close(self):
        """关闭连接"""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
        print("Redis连接已关闭")
    
    def get_client(self) -> aioredis.Redis:
        """获取Redis客户端"""
        if self.client is None:
            raise RuntimeError("Redis未连接，请先调用connect()")
        return self.client


# 全局数据库实例
mongodb = MongoDB()
redis_client = Redis()


async def get_mongodb() -> AsyncIOMotorDatabase:
    """依赖注入：获取MongoDB数据库"""
    return mongodb.get_database()


async def get_redis() -> aioredis.Redis:
    """依赖注入：获取Redis客户端"""
    return redis_client.get_client()

