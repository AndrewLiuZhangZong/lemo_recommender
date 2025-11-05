"""
推荐请求和响应模型
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    """推荐请求"""
    
    scenario_id: str = Field(..., description="场景ID")
    count: int = Field(default=20, ge=1, le=100, description="推荐数量")
    
    # 上下文信息
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="上下文信息（设备、位置等）"
    )
    
    # 过滤条件
    filters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="过滤条件"
    )
    
    # 是否返回调试信息
    debug: bool = Field(default=False, description="是否返回调试信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "scenario_id": "vlog_001",
                "count": 20,
                "context": {
                    "device_type": "mobile",
                    "location": "Beijing"
                },
                "filters": {
                    "exclude_items": ["item_1", "item_2"],
                    "category": "entertainment"
                },
                "debug": False
            }
        }


class RecommendedItem(BaseModel):
    """推荐的物品"""
    
    item_id: str = Field(..., description="物品ID")
    score: float = Field(..., description="推荐分数")
    reason: Optional[str] = Field(None, description="推荐理由")
    strategy: Optional[str] = Field(None, description="召回策略")
    metadata: Optional[Dict[str, Any]] = Field(None, description="物品元数据")


class DebugInfo(BaseModel):
    """调试信息"""
    
    recall_count: int = Field(..., description="召回物品数")
    recall_time_ms: float = Field(..., description="召回耗时（毫秒）")
    rank_time_ms: float = Field(..., description="排序耗时（毫秒）")
    rerank_time_ms: float = Field(..., description="重排耗时（毫秒）")
    total_time_ms: float = Field(..., description="总耗时（毫秒）")
    from_cache: bool = Field(default=False, description="是否来自缓存")
    
    # 各召回策略详情
    recall_strategies: Optional[Dict[str, Any]] = None


class RecommendResponse(BaseModel):
    """推荐响应"""
    
    request_id: str = Field(..., description="请求ID")
    tenant_id: str = Field(..., description="租户ID")
    user_id: str = Field(..., description="用户ID")
    scenario_id: str = Field(..., description="场景ID")
    items: List[RecommendedItem] = Field(..., description="推荐物品列表")
    
    # 调试信息（可选）
    debug_info: Optional[DebugInfo] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_20251022_001",
                "tenant_id": "tenant_001",
                "user_id": "user_001",
                "scenario_id": "vlog_001",
                "items": [
                    {
                        "item_id": "video_100",
                        "score": 0.95,
                        "reason": "基于你的观看历史",
                        "strategy": "collaborative_filtering",
                        "metadata": {
                            "title": "搞笑视频",
                            "duration": 120
                        }
                    }
                ],
                "debug_info": {
                    "recall_count": 250,
                    "recall_time_ms": 15.5,
                    "rank_time_ms": 10.2,
                    "rerank_time_ms": 3.8,
                    "total_time_ms": 35.5
                }
            }
        }

