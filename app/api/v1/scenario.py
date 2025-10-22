"""
场景管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from app.core.database import get_mongodb
from app.api.dependencies import get_tenant_id
from app.models.scenario import (
    Scenario,
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
    ScenarioStatus
)
from app.models.base import PaginationParams, PaginatedResponse, ResponseModel
from app.services.scenario.service import ScenarioService


router = APIRouter()


@router.post("", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    data: ScenarioCreate,
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """创建场景"""
    
    service = ScenarioService(db)
    
    try:
        scenario = await service.create_scenario(tenant_id, data)
        return _to_response(scenario)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=PaginatedResponse)
async def list_scenarios(
    status_filter: Optional[ScenarioStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """查询场景列表"""
    
    service = ScenarioService(db)
    pagination = PaginationParams(page=page, page_size=page_size)
    
    scenarios, total = await service.list_scenarios(
        tenant_id=tenant_id,
        status=status_filter,
        pagination=pagination
    )
    
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_response(s) for s in scenarios]
    )


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """获取场景详情"""
    
    service = ScenarioService(db)
    scenario = await service.get_scenario(tenant_id, scenario_id)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"场景不存在: {scenario_id}"
        )
    
    return _to_response(scenario)


@router.put("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: str,
    data: ScenarioUpdate,
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """更新场景"""
    
    service = ScenarioService(db)
    scenario = await service.update_scenario(tenant_id, scenario_id, data)
    
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"场景不存在: {scenario_id}"
        )
    
    return _to_response(scenario)


@router.delete("/{scenario_id}", response_model=ResponseModel)
async def delete_scenario(
    scenario_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """删除场景"""
    
    service = ScenarioService(db)
    success = await service.delete_scenario(tenant_id, scenario_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"场景不存在: {scenario_id}"
        )
    
    return ResponseModel(message="场景已删除")


@router.post("/{scenario_id}/validate", response_model=ResponseModel)
async def validate_scenario(
    scenario_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """验证场景配置"""
    
    service = ScenarioService(db)
    
    try:
        result = await service.validate_scenario_config(tenant_id, scenario_id)
        return ResponseModel(
            code=200 if result["valid"] else 400,
            message="配置有效" if result["valid"] else "配置无效",
            data=result
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


def _to_response(scenario: Scenario) -> ScenarioResponse:
    """转换为响应模型"""
    return ScenarioResponse(
        id=str(scenario.id),
        tenant_id=scenario.tenant_id,
        scenario_id=scenario.scenario_id,
        scenario_type=scenario.scenario_type.value,
        name=scenario.name,
        description=scenario.description,
        config=scenario.config,
        status=scenario.status.value,
        created_at=scenario.created_at.isoformat(),
        updated_at=scenario.updated_at.isoformat()
    )

