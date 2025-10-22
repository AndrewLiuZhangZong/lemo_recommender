"""
限流器
"""
import time
from typing import Optional
from app.core.redis_client import get_redis_client


class RateLimiter:
    """基于Redis的限流器"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis_client()
    
    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        检查是否允许请求（滑动窗口算法）
        
        Args:
            key: 限流key（如user_id, ip等）
            max_requests: 窗口内最大请求数
            window_seconds: 窗口大小（秒）
            
        Returns:
            是否允许
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Redis key
        rate_limit_key = f"rate_limit:{key}"
        
        # 使用Redis ZSET存储请求时间戳
        pipe = self.redis.pipeline()
        
        # 1. 移除窗口外的记录
        pipe.zremrangebyscore(rate_limit_key, 0, window_start)
        
        # 2. 统计窗口内的请求数
        pipe.zcard(rate_limit_key)
        
        # 3. 添加当前请求
        pipe.zadd(rate_limit_key, {str(now): now})
        
        # 4. 设置过期时间
        pipe.expire(rate_limit_key, window_seconds + 1)
        
        results = pipe.execute()
        
        # 获取当前窗口内的请求数（添加前的数量）
        current_requests = results[1]
        
        return current_requests < max_requests
    
    def get_remaining(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> dict:
        """
        获取剩余请求配额
        
        Returns:
            {
                "remaining": int,  # 剩余请求数
                "reset_at": float  # 重置时间戳
            }
        """
        now = time.time()
        window_start = now - window_seconds
        
        rate_limit_key = f"rate_limit:{key}"
        
        # 移除过期记录并统计
        self.redis.zremrangebyscore(rate_limit_key, 0, window_start)
        current_requests = self.redis.zcard(rate_limit_key)
        
        # 计算重置时间（窗口内最早的请求 + 窗口大小）
        oldest_request = self.redis.zrange(rate_limit_key, 0, 0, withscores=True)
        if oldest_request:
            reset_at = oldest_request[0][1] + window_seconds
        else:
            reset_at = now + window_seconds
        
        return {
            "remaining": max(0, max_requests - current_requests),
            "reset_at": reset_at
        }


class CircuitBreaker:
    """熔断器"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        redis_client=None
    ):
        """
        Args:
            failure_threshold: 失败阈值（连续失败N次后熔断）
            recovery_timeout: 恢复超时时间（秒）
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.redis = redis_client or get_redis_client()
    
    def is_open(self, service_name: str) -> bool:
        """检查熔断器是否打开"""
        key = f"circuit_breaker:{service_name}"
        
        # 获取状态
        state = self.redis.get(key)
        
        if state == b"open":
            # 检查是否到了恢复时间
            open_time_key = f"{key}:open_time"
            open_time = self.redis.get(open_time_key)
            
            if open_time:
                if time.time() - float(open_time) >= self.recovery_timeout:
                    # 进入半开状态
                    self.redis.set(key, "half_open")
                    return False
            
            return True
        
        return False
    
    def record_success(self, service_name: str):
        """记录成功"""
        key = f"circuit_breaker:{service_name}"
        
        # 重置状态和失败计数
        self.redis.delete(key)
        self.redis.delete(f"{key}:failures")
        self.redis.delete(f"{key}:open_time")
    
    def record_failure(self, service_name: str):
        """记录失败"""
        key = f"circuit_breaker:{service_name}"
        failures_key = f"{key}:failures"
        
        # 增加失败计数
        failures = self.redis.incr(failures_key)
        
        # 设置过期时间
        self.redis.expire(failures_key, 60)
        
        # 检查是否达到阈值
        if failures >= self.failure_threshold:
            # 打开熔断器
            self.redis.set(key, "open")
            self.redis.set(f"{key}:open_time", str(time.time()))
            print(f"[CircuitBreaker] {service_name} 熔断器打开")


# 全局实例
rate_limiter = RateLimiter()
circuit_breaker = CircuitBreaker()

