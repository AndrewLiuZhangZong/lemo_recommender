"""
场景配置模型
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

from app.models.base import MongoBaseModel


class ScenarioType(str, Enum):
    """场景类型"""
    VLOG = "vlog"
    NEWS = "news"
    ECOMMERCE = "ecommerce"
    MUSIC = "music"
    CUSTOM = "custom"


class ScenarioStatus(str, Enum):
    """场景状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"


class FeatureConfig(BaseModel):
    """特征配置"""
    name: str
    type: str  # numeric, categorical, multi_categorical, text, timestamp
    weight: float = 1.0
    required: bool = False


class RecallStrategyConfig(BaseModel):
    """召回策略配置"""
    name: str  # user_cf, item_cf, vector_search, hot_items, etc.
    weight: float
    limit: int
    params: Dict[str, Any] = Field(default_factory=dict)


class RankConfig(BaseModel):
    """排序配置"""
    model: str  # deepfm, lightgbm, wide_deep, etc.
    version: str = "v1.0"
    objective: str  # watch_time, click_rate, conversion_rate
    params: Dict[str, Any] = Field(default_factory=dict)
    features: List[str] = Field(default_factory=list)


class RerankRuleConfig(BaseModel):
    """重排规则配置"""
    name: str  # diversity, freshness, quality, business_rule
    weight: float
    params: Dict[str, Any] = Field(default_factory=dict)


class ScenarioConfig(BaseModel):
    """场景配置详情"""
    
    # 特征配置
    features: Dict[str, List[FeatureConfig]] = Field(
        description="特征配置",
        default_factory=lambda: {
            "item_features": [],
            "user_features": [],
            "context_features": []
        }
    )
    
    # 召回配置
    recall: Dict[str, Any] = Field(
        description="召回配置",
        default_factory=lambda: {
            "strategies": [],
            "total_recall_limit": 500,
            "dedup_strategy": "item_id"
        }
    )
    
    # 排序配置
    rank: RankConfig = Field(
        description="排序配置",
        default=RankConfig(model="lightgbm", objective="click_rate")
    )
    
    # 重排配置
    rerank: Dict[str, List[RerankRuleConfig]] = Field(
        description="重排配置",
        default_factory=lambda: {"rules": []}
    )
    
    # 业务规则
    business_rules: Dict[str, Any] = Field(
        description="业务规则",
        default_factory=dict
    )


class Scenario(MongoBaseModel):
    """场景模型（MongoDB文档）"""
    
    tenant_id: str = Field(..., description="租户ID")
    scenario_id: str = Field(..., description="场景ID（租户内唯一）")
    scenario_type: ScenarioType = Field(..., description="场景类型")
    name: str = Field(..., description="场景名称")
    description: Optional[str] = Field(None, description="场景描述")
    config: ScenarioConfig = Field(..., description="场景配置")
    status: ScenarioStatus = Field(default=ScenarioStatus.ACTIVE, description="场景状态")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "tenant_001",
                "scenario_id": "vlog_main_feed",
                "scenario_type": "vlog",
                "name": "短视频主feed流",
                "description": "短视频推荐主场景",
                "config": {
                    "features": {
                        "item_features": [
                            {"name": "duration", "type": "numeric", "weight": 1.0},
                            {"name": "category", "type": "categorical", "weight": 1.5}
                        ]
                    },
                    "recall": {
                        "strategies": [
                            {"name": "user_cf", "weight": 0.3, "limit": 100},
                            {"name": "hot_items", "weight": 0.2, "limit": 50}
                        ]
                    },
                    "rank": {
                        "model": "deepfm",
                        "objective": "watch_time"
                    }
                },
                "status": "active"
            }
        }


# API请求/响应模型
class ScenarioCreate(BaseModel):
    """创建场景请求"""
    scenario_id: str
    scenario_type: ScenarioType
    name: str
    description: Optional[str] = None
    config: ScenarioConfig


class ScenarioUpdate(BaseModel):
    """更新场景请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[ScenarioConfig] = None
    status: Optional[ScenarioStatus] = None


class ScenarioResponse(BaseModel):
    """场景响应"""
    id: str
    tenant_id: str
    scenario_id: str
    scenario_type: str
    name: str
    description: Optional[str]
    config: ScenarioConfig
    status: str
    created_at: str
    updated_at: str

