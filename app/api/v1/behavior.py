"""
行为采集API - v2.0架构

职责：
1. 提供HTTP接口接收埋点数据
2. 强制tenant_id验证（SaaS隔离）
3. 调用BehaviorService处理
4. 返回采集结果
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional
import logging

from app.models.behavior import (
    BehaviorEvent,
    BehaviorEventBatch,
    TrackResponse,
    TrackBatchResponse,
    StatsResponse,
    HealthCheckResponse
)
from app.services.behavior import BehaviorService
from app.api.dependencies import get_behavior_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/behaviors", tags=["Behavior Tracking"])


@router.post(
    "/track",
    response_model=TrackResponse,
    summary="采集单个行为事件",
    description="""
    采集单个用户行为事件（埋点数据）
    
    **SaaS租户隔离 🔒:**
    - `tenant_id` 必填，否则返回400错误
    - 所有事件按`tenant_id`隔离存储
    
    **支持场景:**
    - 短视频：impression, click, play, play_end, like, share
    - 电商：impression, click, view, add_cart, order, payment
    - 新闻：impression, click, read, read_end, like, share
    - 音乐：impression, play, play_end, pause, add_playlist
    - 教育：impression, click, learn, complete, purchase
    
    **数据流:**
    - 验证tenant_id → 发送到Kafka → Flink处理 → ClickHouse存储
    """
)
async def track_event(
    event: BehaviorEvent,
    behavior_service: BehaviorService = Depends(get_behavior_service)
) -> TrackResponse:
    """
    采集单个行为事件
    
    Args:
        event: 行为事件数据
        behavior_service: 行为采集服务（依赖注入）
    
    Returns:
        TrackResponse: 采集结果
    
    Raises:
        HTTPException 400: tenant_id缺失或数据验证失败
        HTTPException 500: 服务内部错误
    """
    try:
        # 调用service处理
        result = await behavior_service.track_event(
            event=event.model_dump(),
            validate_only=False
        )
        
        return TrackResponse(**result)
        
    except ValueError as e:
        # 数据验证失败（如tenant_id缺失）
        logger.warning(f"Event validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # 其他错误
        logger.error(f"Failed to track event: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track event"
        )


@router.post(
    "/track/batch",
    response_model=TrackBatchResponse,
    summary="批量采集行为事件",
    description="""
    批量采集用户行为事件（高性能）
    
    **限制:**
    - 每批最多100条事件
    - 所有事件必须携带`tenant_id`
    
    **适用场景:**
    - 曝光事件批量上报
    - 离线日志补录
    - 数据迁移
    
    **性能:**
    - 批量发送到Kafka
    - 单次请求响应<100ms
    """
)
async def track_batch(
    batch: BehaviorEventBatch,
    behavior_service: BehaviorService = Depends(get_behavior_service)
) -> TrackBatchResponse:
    """
    批量采集行为事件
    
    Args:
        batch: 批量事件数据
        behavior_service: 行为采集服务（依赖注入）
    
    Returns:
        TrackBatchResponse: 批量采集结果
    
    Raises:
        HTTPException 400: 数据验证失败
        HTTPException 500: 服务内部错误
    """
    try:
        # 转换为字典列表
        events = [event.model_dump() for event in batch.events]
        
        # 调用service处理
        result = await behavior_service.track_batch(
            events=events,
            validate_only=False
        )
        
        return TrackBatchResponse(**result)
        
    except ValueError as e:
        logger.warning(f"Batch validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to track batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track batch"
        )


@router.post(
    "/validate",
    response_model=TrackResponse,
    summary="验证行为事件（不发送）",
    description="""
    仅验证事件数据格式，不实际发送到Kafka
    
    **用途:**
    - 调试埋点数据
    - 测试数据格式
    - 集成测试
    """
)
async def validate_event(
    event: BehaviorEvent,
    behavior_service: BehaviorService = Depends(get_behavior_service)
) -> TrackResponse:
    """
    验证事件数据（不发送）
    
    Args:
        event: 行为事件数据
        behavior_service: 行为采集服务（依赖注入）
    
    Returns:
        TrackResponse: 验证结果
    """
    try:
        result = await behavior_service.track_event(
            event=event.model_dump(),
            validate_only=True  # 仅验证，不发送
        )
        
        return TrackResponse(**result)
        
    except ValueError as e:
        logger.warning(f"Event validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="获取采集统计信息",
    description="""
    获取行为采集服务的统计信息
    
    **统计指标:**
    - total_events: 总事件数
    - kafka_success: Kafka发送成功数
    - kafka_failed: Kafka发送失败数
    - rejected: 拒绝数（无tenant_id）
    - success_rate: 成功率（%）
    """
)
async def get_stats(
    behavior_service: BehaviorService = Depends(get_behavior_service)
) -> StatsResponse:
    """获取采集统计信息"""
    try:
        stats = behavior_service.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get stats"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="健康检查",
    description="""
    检查行为采集服务健康状态
    
    **状态类型:**
    - healthy: Kafka可用，服务正常
    - degraded: Kafka不可用，但服务可用（降级）
    - unhealthy: 服务异常
    """
)
async def health_check(
    behavior_service: BehaviorService = Depends(get_behavior_service)
) -> HealthCheckResponse:
    """健康检查"""
    try:
        health = await behavior_service.health_check()
        
        # 根据健康状态返回不同HTTP状态码
        if health["status"] == "healthy":
            return HealthCheckResponse(**health)
        elif health["status"] == "degraded":
            # Kafka不可用但服务可用，返回200但标记为degraded
            return HealthCheckResponse(**health)
        else:
            # 服务异常
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is unhealthy"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed"
        )

