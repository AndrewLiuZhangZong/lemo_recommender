"""
行为采集服务 - 根据v2.0架构重构

职责：
1. 接收前端埋点数据（HTTP/gRPC）
2. 强制tenant_id验证（SaaS隔离）
3. 直接发送到Kafka（不写MongoDB）
4. 返回采集成功响应
"""

from .service import BehaviorService

__all__ = ['BehaviorService']

