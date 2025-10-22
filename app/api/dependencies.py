"""
API依赖注入
"""
from fastapi import Header, HTTPException, status
from typing import Optional


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

