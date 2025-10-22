"""
租户服务gRPC客户端
"""
from typing import Optional
import json


class TenantServiceClient:
    """租户服务gRPC客户端"""
    
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
            # self.stub = TenantServiceStub(self.channel)  # 等待.proto文件定义
            print(f"[gRPC] 租户服务客户端已初始化: {grpc_url}")
            self.enabled = True
        except ImportError:
            print("[gRPC] grpcio未安装，使用模拟模式")
        except Exception as e:
            print(f"[gRPC] 租户服务连接失败: {e}")
    
    async def get_tenant_config(self, tenant_id: str) -> Optional[dict]:
        """
        获取租户配置
        
        Args:
            tenant_id: 租户ID
            
        Returns:
            租户配置字典，如果不存在返回None
        """
        
        # 先从Redis缓存获取
        if self.redis:
            cache_key = f"tenant:config:{tenant_id}"
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached
        
        # 调用gRPC接口
        if self.enabled and self.stub:
            try:
                # request = GetTenantConfigRequest(tenant_id=tenant_id)
                # response = await self.stub.GetTenantConfig(request, timeout=5.0)
                # tenant_config = {
                #     "tenant_id": response.tenant_id,
                #     "tenant_name": response.tenant_name,
                #     "status": response.status,
                #     "quota": response.quota
                # }
                print(f"[gRPC] 调用租户服务: get_tenant_config({tenant_id})")
            except Exception as e:
                print(f"[gRPC] 租户服务调用失败: {e}")
        
        # 模拟数据（在gRPC服务未就绪时使用）
        tenant_config = {
            "tenant_id": tenant_id,
            "tenant_name": f"Tenant-{tenant_id}",
            "status": "active",
            "quota": {
                "max_users": 10000,
                "max_items": 100000,
                "max_requests_per_day": 1000000
            }
        }
        
        # 写入缓存
        if self.redis:
            cache_key = f"tenant:config:{tenant_id}"
            await self._set_to_cache(cache_key, tenant_config, ttl=3600)
        
        return tenant_config
    
    async def validate_tenant(self, tenant_id: str) -> bool:
        """
        验证租户是否有效
        
        Args:
            tenant_id: 租户ID
            
        Returns:
            是否有效
        """
        config = await self.get_tenant_config(tenant_id)
        return config is not None and config.get("status") == "active"
    
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
    
    async def _set_to_cache(self, key: str, value: dict, ttl: int = 3600):
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
                print("[gRPC] 租户服务连接已关闭")
            except Exception as e:
                print(f"[gRPC] 关闭连接失败: {e}")

