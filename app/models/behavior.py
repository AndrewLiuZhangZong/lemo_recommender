"""
行为事件数据模型

符合v2.0架构设计：
- 强制tenant_id（SaaS隔离）
- 支持多场景
- 标准化字段
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime


class ActionType(str, Enum):
    """行为类型枚举"""
    
    # 基础行为
    IMPRESSION = "impression"     # 曝光
    CLICK = "click"               # 点击
    VIEW = "view"                 # 查看详情
    
    # 内容消费
    PLAY = "play"                 # 播放
    PLAY_END = "play_end"         # 播放结束
    READ = "read"                 # 阅读
    READ_END = "read_end"         # 阅读结束
    LEARN = "learn"               # 学习
    COMPLETE = "complete"         # 完成
    
    # 互动行为
    LIKE = "like"                 # 点赞
    DISLIKE = "dislike"           # 踩
    FAVORITE = "favorite"         # 收藏
    SHARE = "share"               # 分享
    COMMENT = "comment"           # 评论
    FOLLOW = "follow"             # 关注
    
    # 交易行为
    ADD_CART = "add_cart"         # 加购物车
    ORDER = "order"               # 下单
    PAYMENT = "payment"           # 支付
    PURCHASE = "purchase"         # 购买
    
    # 其他
    NOT_INTEREST = "not_interest" # 不感兴趣
    PAUSE = "pause"               # 暂停
    REPEAT = "repeat"             # 单曲循环/重播
    DOWNLOAD = "download"         # 下载
    TRIAL = "trial"               # 试用/试看
    NOTE = "note"                 # 做笔记
    ASK = "ask"                   # 提问
    REVIEW = "review"             # 评价
    ADD_PLAYLIST = "add_playlist" # 加入歌单/播放列表


class DeviceType(str, Enum):
    """设备类型"""
    MOBILE = "mobile"
    PC = "pc"
    TABLET = "tablet"
    TV = "tv"
    UNKNOWN = "unknown"


class BehaviorContext(BaseModel):
    """行为上下文信息"""
    
    device_type: DeviceType = Field(..., description="设备类型（必填）")
    os: Optional[str] = Field(None, description="操作系统")
    location: Optional[str] = Field(None, description="地理位置")
    ip: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="User-Agent")
    
    class Config:
        use_enum_values = True


class BehaviorEvent(BaseModel):
    """
    用户行为事件

    SaaS多租户隔离：
    - tenant_id: 必填，用于数据隔离
    - 无tenant_id的请求会被拒绝
    """
    
    # === 核心字段（必填） ===
    tenant_id: str = Field(..., description="租户ID（SaaS必填）")
    scenario_id: str = Field(..., description="场景ID")
    user_id: str = Field(..., description="用户ID")
    item_id: str = Field(..., description="物品ID")
    action_type: ActionType = Field(..., description="行为类型")
    
    # === 系统字段 ===
    event_id: Optional[str] = Field(None, description="事件ID（自动生成）")
    timestamp: Optional[int] = Field(None, description="时间戳毫秒（自动生成）")
    
    # === 上下文信息（必填） ===
    context: BehaviorContext = Field(..., description="行为上下文")
    
    # === 实验相关（可选） ===
    experiment_id: Optional[str] = Field(None, description="AB实验ID")
    experiment_group: Optional[str] = Field(None, description="实验分组")
    
    # === 场景特定字段（可选） ===
    position: Optional[int] = Field(None, description="推荐位置/排位")
    duration: Optional[int] = Field(None, description="内容总时长（秒）")
    watch_duration: Optional[int] = Field(None, description="观看时长（秒）")
    completion_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="完成率（0-1）")
    
    # === 额外数据（JSON） ===
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外数据（场景特定）")
    
    @field_validator('tenant_id', 'scenario_id', 'user_id', 'item_id')
    @classmethod
    def validate_not_empty(cls, v, info):
        """验证字段不能为空"""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()
    
    @field_validator('completion_rate')
    @classmethod
    def validate_completion_rate(cls, v):
        """验证完成率范围"""
        if v is not None and (v < 0 or v > 1):
            raise ValueError("completion_rate must be between 0 and 1")
        return v
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "tenant_id": "mymx",
                "scenario_id": "vlog_feed",
                "user_id": "user_12345",
                "item_id": "item_67890",
                "action_type": "click",
                "context": {
                    "device_type": "mobile",
                    "os": "iOS",
                    "location": "Beijing"
                },
                "position": 3,
                "experiment_id": "exp_001",
                "experiment_group": "treatment"
            }
        }


class BehaviorEventBatch(BaseModel):
    """批量行为事件"""
    
    events: list[BehaviorEvent] = Field(..., min_items=1, max_items=100, description="事件列表（最多100条）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "events": [
                    {
                        "tenant_id": "mymx",
                        "scenario_id": "vlog_feed",
                        "user_id": "user_12345",
                        "item_id": "item_001",
                        "action_type": "impression",
                        "context": {
                            "device_type": "mobile"
                        },
                        "position": 1
                    },
                    {
                        "tenant_id": "mymx",
                        "scenario_id": "vlog_feed",
                        "user_id": "user_12345",
                        "item_id": "item_002",
                        "action_type": "impression",
                        "context": {
                            "device_type": "mobile"
                        },
                        "position": 2
                    }
                ]
            }
        }


class TrackResponse(BaseModel):
    """采集响应"""
    
    success: bool = Field(..., description="是否成功")
    event_id: Optional[str] = Field(None, description="事件ID")
    message: str = Field(..., description="响应消息")


class TrackBatchResponse(BaseModel):
    """批量采集响应"""
    
    success: bool = Field(..., description="整体是否成功")
    total: int = Field(..., description="总数")
    succeeded: int = Field(..., description="成功数")
    failed: int = Field(..., description="失败数")
    errors: list[str] = Field(default_factory=list, description="错误列表")


class StatsResponse(BaseModel):
    """统计响应"""
    
    total_events: int = Field(..., description="总事件数")
    kafka_success: int = Field(..., description="Kafka发送成功数")
    kafka_failed: int = Field(..., description="Kafka发送失败数")
    rejected: int = Field(..., description="拒绝数（缺少tenant_id）")
    success_rate: float = Field(..., description="成功率（%）")


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    
    status: str = Field(..., description="服务状态")
    kafka_available: bool = Field(..., description="Kafka是否可用")
    stats: StatsResponse = Field(..., description="统计信息")

