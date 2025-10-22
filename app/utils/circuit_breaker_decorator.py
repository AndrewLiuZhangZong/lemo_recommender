"""
熔断器装饰器
"""
from functools import wraps
from typing import Optional, Callable, Any
from app.utils.rate_limiter import circuit_breaker


def with_circuit_breaker(
    service_name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    fallback: Optional[Callable] = None
):
    """
    熔断器装饰器
    
    Args:
        service_name: 服务名称
        failure_threshold: 失败阈值
        recovery_timeout: 恢复超时
        fallback: 降级函数
    
    使用示例:
    ```python
    @with_circuit_breaker("external_api", fallback=lambda: {"data": []})
    async def call_external_api():
        return await http_client.get("https://api.example.com")
    ```
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 检查熔断器状态
            if circuit_breaker.is_open(service_name):
                print(f"[CircuitBreaker] {service_name} 熔断中，执行降级")
                if fallback:
                    return fallback() if not asyncio.iscoroutinefunction(fallback) \
                           else await fallback()
                raise Exception(f"服务 {service_name} 熔断中")
            
            try:
                # 执行原函数
                result = await func(*args, **kwargs)
                
                # 记录成功
                circuit_breaker.record_success(service_name)
                
                return result
                
            except Exception as e:
                # 记录失败
                circuit_breaker.record_failure(service_name)
                
                # 执行降级
                if fallback:
                    print(f"[CircuitBreaker] {service_name} 调用失败，执行降级")
                    return fallback() if not asyncio.iscoroutinefunction(fallback) \
                           else await fallback()
                
                raise
        
        return wrapper
    return decorator


import asyncio

