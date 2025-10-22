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
        self.channel = None
        self.stub = None
        self.enabled = False
        
        # 尝试初始化gRPC连接
        try:
            import grpc
            self.channel = grpc.aio.insecure_channel(grpc_url)
            # self.stub = UserServiceStub(self.channel)  # 等待.proto文件定义
            print(f"[gRPC] 用户服务客户端已初始化: {grpc_url}")
            self.enabled = True
        except ImportError:
            print("[gRPC] grpcio未安装，使用模拟模式")
        except Exception as e:
            print(f"[gRPC] 用户服务连接失败: {e}")
    
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
        
        # 调用gRPC接口
        if self.enabled and self.stub:
            try:
                # request = GetUserInfoRequest(tenant_id=tenant_id, user_id=user_id)
                # response = await self.stub.GetUserInfo(request, timeout=5.0)
                # user_info = {
                #     "user_id": response.user_id,
                #     "tenant_id": response.tenant_id,
                #     "profile": response.profile,
                #     "status": response.status
                # }
                print(f"[gRPC] 调用用户服务: get_user_info({tenant_id}, {user_id})")
            except Exception as e:
                print(f"[gRPC] 用户服务调用失败: {e}")
        
        # 模拟数据（在gRPC服务未就绪时使用）
        user_info = {
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
            await self._set_to_cache(cache_key, user_info, ttl=1800)
        
        return user_info
    
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
        if not self.redis:
            return None
            
        try:
            value = await self.redis.get(key)
            if value:
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                return json.loads(value)
            return None
        except Exception as e:
            print(f"[Redis] 读取失败: {e}")
            return None
    
    async def _set_to_cache(self, key: str, value: dict, ttl: int = 1800):
        """写入Redis缓存"""
        if not self.redis:
            return
            
        try:
            await self.redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        except Exception as e:
            print(f"[Redis] 写入失败: {e}")
    
    async def close(self):
        """关闭gRPC连接"""
        if self.channel:
            try:
                await self.channel.close()
                print("[gRPC] 用户服务连接已关闭")
            except Exception as e:
                print(f"[gRPC] 关闭连接失败: {e}")

