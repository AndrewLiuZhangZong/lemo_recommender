"""
用户画像模型
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.base import MongoBaseModel


class UserProfile(MongoBaseModel):
    """用户画像模型（MongoDB文档）"""
    
    tenant_id: str = Field(..., description="租户ID")
    user_id: str = Field(..., description="用户ID")
    scenario_id: str = Field(..., description="场景ID")
    
    # 用户特征（统计特征）
    features: Dict[str, Any] = Field(
        default_factory=dict,
        description="用户特征（统计值）"
    )
    
    # 用户偏好（标签和分数）
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="用户偏好（分类、标签偏好分数）"
    )
    
    # 用户向量表示
    embedding: Optional[List[float]] = Field(None, description="用户向量表示")
    
    # 最后交互时间
    last_interaction_time: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "tenant_001",
                "user_id": "user_001",
                "scenario_id": "vlog_001",
                "features": {
                    "total_watch_count": 100,
                    "avg_watch_duration": 90,
                    "favorite_categories": ["entertainment", "sports"],
                    "active_time_slots": ["morning", "night"],
                    "preferred_video_duration": 120,
                    "preferred_authors": ["author_001", "author_002"]
                },
                "preferences": {
                    "category_scores": {
                        "entertainment": 0.8,
                        "sports": 0.6,
                        "news": 0.3
                    },
                    "tag_scores": {
                        "funny": 0.9,
                        "comedy": 0.7
                    }
                },
                "last_interaction_time": "2025-10-22T10:00:00Z"
            }
        }


# API响应模型
class UserProfileResponse(BaseModel):
    """用户画像响应"""
    id: str
    tenant_id: str
    user_id: str
    scenario_id: str
    features: Dict[str, Any]
    preferences: Dict[str, Any]
    last_interaction_time: Optional[str]
    updated_at: str

