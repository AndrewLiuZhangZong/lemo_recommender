"""
用户行为模型
"""
from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from app.models.base import MongoBaseModel


class ActionType(str, Enum):
    """行为类型"""
    IMPRESSION = "impression"  # 曝光
    CLICK = "click"  # 点击
    VIEW = "view"  # 观看
    LIKE = "like"  # 点赞
    FAVORITE = "favorite"  # 收藏
    SHARE = "share"  # 分享
    COMMENT = "comment"  # 评论
    SKIP = "skip"  # 跳过


class Interaction(MongoBaseModel):
    """用户行为模型（MongoDB文档）"""
    
    tenant_id: str = Field(..., description="租户ID")
    scenario_id: str = Field(..., description="场景ID")
    user_id: str = Field(..., description="用户ID")
    item_id: str = Field(..., description="物品ID")
    action_type: ActionType = Field(..., description="行为类型")
    
    # 上下文信息
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="上下文信息（设备、位置等）"
    )
    
    # 场景特定的额外信息
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="额外信息（场景特定）"
    )
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="行为时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "tenant_001",
                "scenario_id": "vlog_001",
                "user_id": "user_001",
                "item_id": "video_12345",
                "action_type": "view",
                "context": {
                    "device_type": "mobile",
                    "os": "iOS",
                    "location": "Beijing",
                    "time_of_day": "morning"
                },
                "extra": {
                    "watch_duration": 90,
                    "completion_rate": 0.75,
                    "is_finished": False
                },
                "timestamp": "2025-10-22T10:00:00Z"
            }
        }


# API请求/响应模型
class InteractionCreate(BaseModel):
    """上报行为请求"""
    scenario_id: str
    user_id: str
    item_id: str
    action_type: ActionType
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None


class InteractionBatchCreate(BaseModel):
    """批量上报行为请求"""
    interactions: List[InteractionCreate] = Field(..., description="行为列表")


class InteractionResponse(BaseModel):
    """行为响应"""
    id: str
    tenant_id: str
    scenario_id: str
    user_id: str
    item_id: str
    action_type: str
    context: Dict[str, Any]
    extra: Dict[str, Any]
    timestamp: str

