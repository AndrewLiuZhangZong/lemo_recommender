"""
推荐服务API
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_mongodb
from app.api.dependencies import get_tenant_id, get_user_id, get_request_id
from app.models.recommendation import RecommendRequest, RecommendResponse
from app.services.recommendation.service import RecommendationService


router = APIRouter()


@router.post("", response_model=RecommendResponse)
async def recommend(
    request: RecommendRequest,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id),
    request_id: str = Depends(get_request_id),
    db = Depends(get_mongodb)
):
    """
    推荐接口
    
    根据用户ID和场景ID返回个性化推荐结果
    """
    
    service = RecommendationService(db)
    
    try:
        response = await service.recommend(
            tenant_id=tenant_id,
            user_id=user_id,
            request=request
        )
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"推荐失败: {str(e)}"
        )

