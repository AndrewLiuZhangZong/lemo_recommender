"""
行为采集API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List

from app.core.database import get_mongodb
from app.api.dependencies import get_tenant_id, get_user_id
from app.models.interaction import (
    Interaction,
    InteractionCreate,
    InteractionBatchCreate,
    InteractionResponse,
    ActionType
)
from app.models.base import ResponseModel
from app.services.interaction.service import InteractionService


router = APIRouter()


@router.post("", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
async def record_interaction(
    data: InteractionCreate,
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """记录用户行为"""
    
    service = InteractionService(db)
    
    try:
        interaction = await service.record_interaction(tenant_id, data)
        return _to_response(interaction)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/batch", response_model=ResponseModel)
async def batch_record_interactions(
    data: InteractionBatchCreate,
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """批量记录用户行为"""
    
    service = InteractionService(db)
    
    try:
        count = await service.batch_record_interactions(
            tenant_id=tenant_id,
            interactions=data.interactions
        )
        return ResponseModel(
            message=f"成功记录{count}条行为",
            data={"count": count}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/user/{user_id}", response_model=List[InteractionResponse])
async def get_user_interactions(
    user_id: str,
    scenario_id: Optional[str] = Query(None),
    action_types: Optional[str] = Query(None, description="逗号分隔的行为类型"),
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """获取用户行为记录"""
    
    service = InteractionService(db)
    
    # 解析action_types
    action_type_list = None
    if action_types:
        action_type_list = [ActionType(t.strip()) for t in action_types.split(",")]
    
    interactions = await service.get_user_interactions(
        tenant_id=tenant_id,
        user_id=user_id,
        scenario_id=scenario_id,
        action_types=action_type_list,
        hours=hours,
        limit=limit
    )
    
    return [_to_response(i) for i in interactions]


@router.get("/item/{scenario_id}/{item_id}", response_model=List[InteractionResponse])
async def get_item_interactions(
    scenario_id: str,
    item_id: str,
    action_types: Optional[str] = Query(None, description="逗号分隔的行为类型"),
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """获取物品行为记录"""
    
    service = InteractionService(db)
    
    # 解析action_types
    action_type_list = None
    if action_types:
        action_type_list = [ActionType(t.strip()) for t in action_types.split(",")]
    
    interactions = await service.get_item_interactions(
        tenant_id=tenant_id,
        item_id=item_id,
        scenario_id=scenario_id,
        action_types=action_type_list,
        hours=hours,
        limit=limit
    )
    
    return [_to_response(i) for i in interactions]


@router.get("/stats/{scenario_id}", response_model=ResponseModel)
async def get_interaction_stats(
    scenario_id: str,
    hours: int = Query(24, ge=1, le=168),
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """获取行为统计"""
    
    service = InteractionService(db)
    
    stats = await service.get_interaction_stats(
        tenant_id=tenant_id,
        scenario_id=scenario_id,
        hours=hours
    )
    
    return ResponseModel(
        message="统计成功",
        data=stats
    )


def _to_response(interaction: Interaction) -> InteractionResponse:
    """转换为响应模型"""
    return InteractionResponse(
        id=str(interaction.id),
        tenant_id=interaction.tenant_id,
        scenario_id=interaction.scenario_id,
        user_id=interaction.user_id,
        item_id=interaction.item_id,
        action_type=interaction.action_type.value,
        context=interaction.context,
        extra=interaction.extra,
        timestamp=interaction.timestamp.isoformat()
    )

