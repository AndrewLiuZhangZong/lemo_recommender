"""
推荐服务API - v2.0 BFF编排层
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.api.dependencies import get_tenant_id, get_user_id
from app.services.recommendation.bff_service import get_bff_service


router = APIRouter()


class RecommendRequestV2(BaseModel):
    """推荐请求"""
    scenario_id: str
    count: int = 20
    filters: Optional[Dict] = None
    debug: bool = False


class RecommendedItemV2(BaseModel):
    """推荐物品"""
    item_id: str
    score: float


class RecommendResponseV2(BaseModel):
    """推荐响应"""
    items: List[RecommendedItemV2]
    count: int
    request_id: str
    debug_info: Optional[Dict] = None
    error: Optional[str] = None


@router.post("/v2", response_model=RecommendResponseV2)
async def recommend_v2(
    request: RecommendRequestV2,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id)
):
    """
    推荐接口 v2.0 - BFF编排层
    
    通过gRPC调用召回→精排→重排微服务
    """
    bff_service = get_bff_service()
    
    try:
        result = await bff_service.get_recommendations(
            tenant_id=tenant_id,
            scenario_id=request.scenario_id,
            user_id=user_id,
            count=request.count,
            filters=request.filters,
            debug=request.debug
        )
        
        # 转换响应格式
        items = [
            RecommendedItemV2(item_id=item["item_id"], score=item["score"])
            for item in result.get("items", [])
        ]
        
        return RecommendResponseV2(
            items=items,
            count=result.get("count", 0),
            request_id=result.get("request_id", ""),
            debug_info=result.get("debug_info"),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"推荐失败: {str(e)}"
        )

