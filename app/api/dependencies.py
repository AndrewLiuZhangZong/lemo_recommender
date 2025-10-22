"""
API依赖注入
"""
from fastapi import Header, HTTPException, status, Depends
from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase


async def get_tenant_id(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id")
) -> str:
    """
    从请求头获取租户ID
    网关已完成认证，这里直接读取Header
    """
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少租户ID (X-Tenant-Id header)"
        )
    return x_tenant_id


async def get_user_id(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> str:
    """
    从请求头获取用户ID
    网关已完成认证，这里直接读取Header
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少用户ID (X-User-Id header)"
        )
    return x_user_id


async def get_request_id(
    x_request_id: Optional[str] = Header(None, alias="X-Request-Id")
) -> Optional[str]:
    """从请求头获取请求追踪ID"""
    return x_request_id


async def get_tenant_user_context(
    tenant_id: str = Depends(get_tenant_id),
    user_id: Optional[str] = Header(None, alias="X-User-Id"),
    request_id: Optional[str] = Depends(get_request_id)
) -> Dict[str, Optional[str]]:
    """
    获取租户和用户上下文信息
    返回包含 tenant_id, user_id, request_id 的字典
    """
    return {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "request_id": request_id
    }


async def get_mongodb() -> AsyncIOMotorDatabase:
    """获取MongoDB数据库连接"""
    from app.core.database import get_mongodb as _get_mongodb
    return _get_mongodb()

