"""
物品模型
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

from app.models.base import MongoBaseModel


class ItemStatus(str, Enum):
    """物品状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class Item(MongoBaseModel):
    """物品模型（MongoDB文档）"""
    
    tenant_id: str = Field(..., description="租户ID")
    scenario_id: str = Field(..., description="场景ID")
    item_id: str = Field(..., description="物品ID（场景内唯一）")
    
    # 物品元数据（灵活Schema，不同场景字段不同）
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="物品元数据（场景特定字段）"
    )
    
    # 向量表示（可选，也可存储在Milvus）
    embedding: Optional[List[float]] = Field(None, description="物品向量表示")
    
    status: ItemStatus = Field(default=ItemStatus.ACTIVE, description="物品状态")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "tenant_001",
                "scenario_id": "vlog_001",
                "item_id": "video_12345",
                "metadata": {
                    # vlog场景特有字段
                    "title": "搞笑视频合集",
                    "duration": 120,
                    "category": "entertainment",
                    "tags": ["funny", "comedy"],
                    "author_id": "author_001",
                    "cover_url": "https://example.com/cover.jpg",
                    "publish_time": "2025-10-20T10:00:00Z",
                    "view_count": 10000,
                    "like_count": 500,
                    "completion_rate": 0.85
                },
                "status": "active"
            }
        }


# API请求/响应模型
class ItemCreate(BaseModel):
    """创建物品请求"""
    scenario_id: str
    item_id: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class ItemUpdate(BaseModel):
    """更新物品请求"""
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None
    status: Optional[ItemStatus] = None


class ItemBatchCreate(BaseModel):
    """批量创建物品请求"""
    scenario_id: str
    items: List[Dict[str, Any]] = Field(..., description="物品列表")


class ItemResponse(BaseModel):
    """物品响应"""
    id: str
    tenant_id: str
    scenario_id: str
    item_id: str
    metadata: Dict[str, Any]
    status: str
    created_at: str
    updated_at: str


class ItemListQuery(BaseModel):
    """物品查询参数"""
    scenario_id: Optional[str] = None
    status: Optional[ItemStatus] = None
    category: Optional[str] = None  # 从metadata中筛选

