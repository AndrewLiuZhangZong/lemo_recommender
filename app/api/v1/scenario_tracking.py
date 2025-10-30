"""
场景埋点配置管理API

提供场景埋点配置的CRUD接口和模板管理
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
import logging

from app.models.scenario_tracking import (
    ScenarioTrackingConfig,
    ScenarioTrackingTemplate,
    ScenarioType,
    BUILT_IN_TEMPLATES
)
from app.services.scenario_tracking import ScenarioTrackingService
from app.api.dependencies import get_tracking_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tracking-configs", tags=["Scenario Tracking Config"])


@router.post(
    "/",
    response_model=dict,
    summary="创建场景埋点配置",
    description="""
    创建场景埋点配置，定义特定场景需要采集的字段和验证规则。
    
    **使用场景:**
    - 新建场景时配置埋点字段
    - 自定义场景的埋点数据结构
    - 从模板创建配置
    
    **注意:**
    - 一个场景只能有一个埋点配置
    - 配置创建后可以更新但不能删除（软删除）
    """
)
async def create_tracking_config(
    config: ScenarioTrackingConfig,
    tracking_service: ScenarioTrackingService = Depends(get_tracking_service)
):
    """创建场景埋点配置"""
    try:
        result = await tracking_service.create_config(
            tenant_id=config.tenant_id,
            scenario_id=config.scenario_id,
            scenario_type=config.scenario_type,
            name=config.name,
            required_fields=[f.model_dump() for f in config.required_fields],
            optional_fields=[f.model_dump() for f in config.optional_fields],
            recommended_actions=config.recommended_actions,
            description=config.description,
            created_by=config.created_by
        )
        
        return {
            "success": True,
            "message": "Tracking config created successfully",
            "data": result
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create tracking config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tracking config"
        )


@router.get(
    "/{tenant_id}/{scenario_id}",
    response_model=dict,
    summary="获取场景埋点配置",
    description="获取指定租户和场景的埋点配置"
)
async def get_tracking_config(
    tenant_id: str,
    scenario_id: str,
    tracking_service: ScenarioTrackingService = Depends(get_tracking_service)
):
    """获取场景埋点配置"""
    try:
        config = await tracking_service.get_config(
            tenant_id=tenant_id,
            scenario_id=scenario_id
        )
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tracking config not found for {tenant_id}/{scenario_id}"
            )
        
        return {
            "success": True,
            "data": config
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tracking config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tracking config"
        )


@router.get(
    "/",
    response_model=dict,
    summary="列出场景埋点配置",
    description="""
    查询场景埋点配置列表，支持多种筛选条件。
    
    **筛选条件:**
    - tenant_id: 按租户筛选
    - scenario_type: 按场景类型筛选（video/ecommerce/news/music/education）
    - is_active: 是否启用
    """
)
async def list_tracking_configs(
    tenant_id: Optional[str] = Query(None, description="租户ID"),
    scenario_type: Optional[str] = Query(None, description="场景类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    tracking_service: ScenarioTrackingService = Depends(get_tracking_service)
):
    """列出场景埋点配置"""
    try:
        result = await tracking_service.list_configs(
            tenant_id=tenant_id,
            scenario_type=scenario_type,
            is_active=is_active,
            skip=skip,
            limit=limit
        )
        
        return {
            "success": True,
            "data": result
        }
    
    except Exception as e:
        logger.error(f"Failed to list tracking configs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tracking configs"
        )


@router.put(
    "/{tenant_id}/{scenario_id}",
    response_model=dict,
    summary="更新场景埋点配置",
    description="更新指定场景的埋点配置"
)
async def update_tracking_config(
    tenant_id: str,
    scenario_id: str,
    updates: dict,
    tracking_service: ScenarioTrackingService = Depends(get_tracking_service)
):
    """更新场景埋点配置"""
    try:
        result = await tracking_service.update_config(
            tenant_id=tenant_id,
            scenario_id=scenario_id,
            updates=updates
        )
        
        return {
            "success": True,
            "message": "Tracking config updated successfully",
            "data": result
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update tracking config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tracking config"
        )


@router.delete(
    "/{tenant_id}/{scenario_id}",
    response_model=dict,
    summary="删除场景埋点配置",
    description="删除指定场景的埋点配置（软删除）"
)
async def delete_tracking_config(
    tenant_id: str,
    scenario_id: str,
    tracking_service: ScenarioTrackingService = Depends(get_tracking_service)
):
    """删除场景埋点配置"""
    try:
        success = await tracking_service.delete_config(
            tenant_id=tenant_id,
            scenario_id=scenario_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tracking config not found: {tenant_id}/{scenario_id}"
            )
        
        return {
            "success": True,
            "message": "Tracking config deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete tracking config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete tracking config"
        )


@router.post(
    "/from-template",
    response_model=dict,
    summary="从模板创建配置",
    description="""
    从预定义模板创建场景埋点配置。
    
    **内置模板:**
    - video: 视频场景（短视频、vlog等）
    - ecommerce: 电商场景
    - news: 新闻/文章场景
    - music: 音乐场景
    - education: 在线教育场景
    """
)
async def create_from_template(
    tenant_id: str = Query(..., description="租户ID"),
    scenario_id: str = Query(..., description="场景ID"),
    template_id: str = Query(..., description="模板ID"),
    name: Optional[str] = Query(None, description="配置名称"),
    created_by: Optional[str] = Query(None, description="创建人"),
    tracking_service: ScenarioTrackingService = Depends(get_tracking_service)
):
    """从模板创建配置"""
    try:
        result = await tracking_service.create_from_template(
            tenant_id=tenant_id,
            scenario_id=scenario_id,
            template_id=template_id,
            name=name,
            created_by=created_by
        )
        
        return {
            "success": True,
            "message": "Tracking config created from template",
            "data": result
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create from template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create from template"
        )


@router.get(
    "/templates/",
    response_model=dict,
    summary="列出场景模板",
    description="""
    获取可用的场景埋点模板列表。
    
    包括内置模板和自定义模板。
    """
)
async def list_templates(
    scenario_type: Optional[str] = Query(None, description="场景类型"),
    is_official: Optional[bool] = Query(None, description="是否官方模板"),
    tracking_service: ScenarioTrackingService = Depends(get_tracking_service)
):
    """列出场景模板"""
    try:
        templates = await tracking_service.list_templates(
            scenario_type=scenario_type,
            is_official=is_official
        )
        
        return {
            "success": True,
            "data": {
                "templates": templates,
                "total": len(templates)
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to list templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list templates"
        )


@router.get(
    "/templates/{template_id}",
    response_model=dict,
    summary="获取模板详情",
    description="获取指定模板的详细配置"
)
async def get_template(
    template_id: str,
    tracking_service: ScenarioTrackingService = Depends(get_tracking_service)
):
    """获取模板详情"""
    try:
        template = await tracking_service.get_template(template_id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found: {template_id}"
            )
        
        return {
            "success": True,
            "data": template
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get template"
        )


@router.get(
    "/templates/built-in/all",
    response_model=dict,
    summary="获取所有内置模板",
    description="获取系统预定义的所有内置模板"
)
async def get_built_in_templates(
    tracking_service: ScenarioTrackingService = Depends(get_tracking_service)
):
    """获取所有内置模板"""
    try:
        templates = tracking_service.get_built_in_templates()
        
        return {
            "success": True,
            "data": {
                "templates": templates,
                "total": len(templates)
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get built-in templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get built-in templates"
        )

