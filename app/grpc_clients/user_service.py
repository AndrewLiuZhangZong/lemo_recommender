"""
用户服务gRPC客户端
"""
from typing import Optional
import json


class UserServiceClient:
    """用户服务gRPC客户端"""
    
    def __init__(self, grpc_url: str, redis_client=None):
        self.grpc_url = grpc_url
        self.redis = redis_client
        # TODO: 初始化gRPC连接
        # self.channel = grpc.aio.insecure_channel(grpc_url)
        # self.stub = UserServiceStub(self.channel)
    
    async def get_user_info(self, tenant_id: str, user_id: str) -> Optional[dict]:
        """
        获取用户信息
        
        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            
        Returns:
            用户信息字典，如果不存在返回None
        """
        
        # 先从Redis缓存获取
        if self.redis:
            cache_key = f"user:info:{tenant_id}:{user_id}"
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached
        
        # TODO: 调用gRPC接口
        # request = GetUserInfoRequest(tenant_id=tenant_id, user_id=user_id)
        # response = await self.stub.GetUserInfo(request, timeout=5.0)
        
        # 临时模拟数据（等待实际gRPC服务）
        mock_info = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "profile": {
                "age": "25-34",
                "gender": "male",
                "location": "Beijing"
            },
            "status": "active"
        }
        
        # 写入缓存
        if self.redis:
            cache_key = f"user:info:{tenant_id}:{user_id}"
            await self._set_to_cache(cache_key, mock_info, ttl=1800)
        
        return mock_info
    
    async def validate_user(self, tenant_id: str, user_id: str) -> bool:
        """
        验证用户是否有效
        
        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            
        Returns:
            是否有效
        """
        info = await self.get_user_info(tenant_id, user_id)
        return info is not None and info.get("status") == "active"
    
    async def _get_from_cache(self, key: str) -> Optional[dict]:
        """从Redis缓存获取"""
        try:
            # TODO: 实际Redis实现
            # value = await self.redis.get(key)
            # if value:
            #     return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis读取失败: {e}")
            return None
    
    async def _set_to_cache(self, key: str, value: dict, ttl: int = 1800):
        """写入Redis缓存"""
        try:
            # TODO: 实际Redis实现
            # await self.redis.setex(key, ttl, json.dumps(value))
            pass
        except Exception as e:
            print(f"Redis写入失败: {e}")
    
    async def close(self):
        """关闭gRPC连接"""
        # TODO: 关闭channel
        # await self.channel.close()
        pass

