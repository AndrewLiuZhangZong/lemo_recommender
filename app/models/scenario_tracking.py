"""
场景埋点配置数据模型

用于定义不同业务场景的埋点数据结构和验证规则
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime


class FieldType(str, Enum):
    """字段类型枚举"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    ARRAY_STRING = "array_string"
    ARRAY_INTEGER = "array_integer"
    JSON = "json"


class FieldValidation(BaseModel):
    """字段验证规则"""
    
    field_name: str = Field(..., description="字段名称")
    field_type: FieldType = Field(..., description="字段类型")
    required: bool = Field(False, description="是否必填")
    description: str = Field("", description="字段描述")
    
    # 数值类型验证
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    
    # 字符串类型验证
    min_length: Optional[int] = Field(None, description="最小长度")
    max_length: Optional[int] = Field(None, description="最大长度")
    pattern: Optional[str] = Field(None, description="正则表达式")
    
    # 枚举验证
    enum_values: Optional[List[str]] = Field(None, description="枚举值列表")
    
    # 默认值
    default_value: Optional[Any] = Field(None, description="默认值")
    
    class Config:
        use_enum_values = True


class ScenarioType(str, Enum):
    """场景类型枚举"""
    VIDEO = "video"              # 视频场景（短视频、vlog等）
    ECOMMERCE = "ecommerce"      # 电商场景
    NEWS = "news"                # 新闻/文章场景
    MUSIC = "music"              # 音乐场景
    EDUCATION = "education"      # 教育/课程场景
    CUSTOM = "custom"            # 自定义场景
    
    class Config:
        use_enum_values = True


class ScenarioTrackingConfig(BaseModel):
    """
    场景埋点配置
    
    定义特定场景需要采集的字段和验证规则
    """
    
    config_id: Optional[str] = Field(None, description="配置ID（自动生成）")
    tenant_id: str = Field(..., description="租户ID")
    scenario_id: str = Field(..., description="场景ID")
    scenario_type: ScenarioType = Field(..., description="场景类型")
    
    name: str = Field(..., description="配置名称")
    description: str = Field("", description="配置描述")
    
    # 字段定义
    required_fields: List[FieldValidation] = Field(
        default_factory=list,
        description="必填字段列表"
    )
    optional_fields: List[FieldValidation] = Field(
        default_factory=list,
        description="可选字段列表"
    )
    
    # 推荐的行为类型
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="推荐的行为类型列表"
    )
    
    # 配置状态
    is_active: bool = Field(True, description="是否启用")
    version: str = Field("1.0", description="配置版本")
    
    # 元数据
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建人")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "mymx",
                "scenario_id": "vlog_feed",
                "scenario_type": "video",
                "name": "短视频埋点配置",
                "description": "短视频feed流的埋点数据配置",
                "required_fields": [
                    {
                        "field_name": "duration",
                        "field_type": "integer",
                        "required": True,
                        "description": "视频总时长（秒）",
                        "min_value": 1,
                        "max_value": 3600
                    },
                    {
                        "field_name": "watch_duration",
                        "field_type": "integer",
                        "required": True,
                        "description": "观看时长（秒）",
                        "min_value": 0
                    }
                ],
                "optional_fields": [
                    {
                        "field_name": "video_quality",
                        "field_type": "string",
                        "required": False,
                        "description": "视频质量",
                        "enum_values": ["360p", "480p", "720p", "1080p", "4K"]
                    }
                ],
                "recommended_actions": [
                    "impression",
                    "click",
                    "play",
                    "play_end",
                    "like",
                    "share"
                ]
            }
        }


class ScenarioTrackingTemplate(BaseModel):
    """
    场景埋点模板
    
    预定义的常见场景埋点配置模板
    """
    
    template_id: str = Field(..., description="模板ID")
    scenario_type: ScenarioType = Field(..., description="场景类型")
    name: str = Field(..., description="模板名称")
    description: str = Field("", description="模板描述")
    
    # 模板配置
    config: Dict[str, Any] = Field(..., description="配置内容（JSON）")
    
    # 标签
    tags: List[str] = Field(default_factory=list, description="标签")
    
    # 适用行业
    industries: List[str] = Field(default_factory=list, description="适用行业")
    
    # 模板元数据
    is_official: bool = Field(True, description="是否官方模板")
    usage_count: int = Field(0, description="使用次数")
    
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class TrackingValidationResult(BaseModel):
    """埋点数据验证结果"""
    
    is_valid: bool = Field(..., description="是否验证通过")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    missing_fields: List[str] = Field(default_factory=list, description="缺失字段")
    invalid_fields: Dict[str, str] = Field(
        default_factory=dict,
        description="无效字段（字段名: 错误原因）"
    )


# 预定义场景模板
BUILT_IN_TEMPLATES = {
    "video": {
        "template_id": "video_default",
        "scenario_type": "video",
        "name": "视频场景标准模板",
        "description": "适用于短视频、vlog、视频课程等场景",
        "config": {
            "required_fields": [
                {
                    "field_name": "duration",
                    "field_type": "integer",
                    "required": True,
                    "description": "视频总时长（秒）",
                    "min_value": 1,
                    "max_value": 7200
                },
                {
                    "field_name": "watch_duration",
                    "field_type": "integer",
                    "required": True,
                    "description": "观看时长（秒）",
                    "min_value": 0
                },
                {
                    "field_name": "completion_rate",
                    "field_type": "float",
                    "required": True,
                    "description": "完成率（0-1）",
                    "min_value": 0.0,
                    "max_value": 1.0
                }
            ],
            "optional_fields": [
                {
                    "field_name": "video_quality",
                    "field_type": "string",
                    "required": False,
                    "description": "视频质量",
                    "enum_values": ["360p", "480p", "720p", "1080p", "2K", "4K"]
                },
                {
                    "field_name": "is_fullscreen",
                    "field_type": "boolean",
                    "required": False,
                    "description": "是否全屏"
                },
                {
                    "field_name": "playback_speed",
                    "field_type": "float",
                    "required": False,
                    "description": "播放速度",
                    "enum_values": ["0.5", "0.75", "1.0", "1.25", "1.5", "2.0"]
                }
            ],
            "recommended_actions": [
                "impression", "click", "play", "play_end",
                "pause", "like", "share", "comment", "favorite"
            ]
        },
        "tags": ["video", "vlog", "short-video"],
        "industries": ["社交", "娱乐", "教育"]
    },
    
    "ecommerce": {
        "template_id": "ecommerce_default",
        "scenario_type": "ecommerce",
        "name": "电商场景标准模板",
        "description": "适用于商品推荐、购物车、订单等场景",
        "config": {
            "required_fields": [
                {
                    "field_name": "price",
                    "field_type": "float",
                    "required": True,
                    "description": "商品价格",
                    "min_value": 0.0
                },
                {
                    "field_name": "category_path",
                    "field_type": "string",
                    "required": True,
                    "description": "商品分类路径"
                }
            ],
            "optional_fields": [
                {
                    "field_name": "brand",
                    "field_type": "string",
                    "required": False,
                    "description": "品牌"
                },
                {
                    "field_name": "quantity",
                    "field_type": "integer",
                    "required": False,
                    "description": "购买数量",
                    "min_value": 1
                },
                {
                    "field_name": "discount",
                    "field_type": "float",
                    "required": False,
                    "description": "折扣率（0-1）",
                    "min_value": 0.0,
                    "max_value": 1.0
                }
            ],
            "recommended_actions": [
                "impression", "click", "view", "add_cart",
                "order", "payment", "purchase", "favorite", "share"
            ]
        },
        "tags": ["ecommerce", "shopping", "retail"],
        "industries": ["电商", "零售"]
    },
    
    "news": {
        "template_id": "news_default",
        "scenario_type": "news",
        "name": "新闻资讯场景标准模板",
        "description": "适用于新闻、文章、资讯等场景",
        "config": {
            "required_fields": [
                {
                    "field_name": "read_duration",
                    "field_type": "integer",
                    "required": True,
                    "description": "阅读时长（秒）",
                    "min_value": 0
                },
                {
                    "field_name": "word_count",
                    "field_type": "integer",
                    "required": True,
                    "description": "文章字数",
                    "min_value": 0
                }
            ],
            "optional_fields": [
                {
                    "field_name": "read_progress",
                    "field_type": "float",
                    "required": False,
                    "description": "阅读进度（0-1）",
                    "min_value": 0.0,
                    "max_value": 1.0
                },
                {
                    "field_name": "news_type",
                    "field_type": "string",
                    "required": False,
                    "description": "新闻类型",
                    "enum_values": ["时政", "财经", "科技", "娱乐", "体育", "社会"]
                },
                {
                    "field_name": "source",
                    "field_type": "string",
                    "required": False,
                    "description": "新闻来源"
                }
            ],
            "recommended_actions": [
                "impression", "click", "read", "read_end",
                "like", "share", "comment", "favorite"
            ]
        },
        "tags": ["news", "article", "content"],
        "industries": ["媒体", "资讯"]
    },
    
    "music": {
        "template_id": "music_default",
        "scenario_type": "music",
        "name": "音乐场景标准模板",
        "description": "适用于音乐播放、歌单推荐等场景",
        "config": {
            "required_fields": [
                {
                    "field_name": "duration",
                    "field_type": "integer",
                    "required": True,
                    "description": "歌曲总时长（秒）",
                    "min_value": 1
                },
                {
                    "field_name": "play_duration",
                    "field_type": "integer",
                    "required": True,
                    "description": "播放时长（秒）",
                    "min_value": 0
                }
            ],
            "optional_fields": [
                {
                    "field_name": "artist",
                    "field_type": "string",
                    "required": False,
                    "description": "艺术家"
                },
                {
                    "field_name": "genre",
                    "field_type": "string",
                    "required": False,
                    "description": "音乐风格",
                    "enum_values": ["流行", "摇滚", "民谣", "古典", "电子", "说唱"]
                },
                {
                    "field_name": "audio_quality",
                    "field_type": "string",
                    "required": False,
                    "description": "音质",
                    "enum_values": ["标准", "高品", "无损", "Hi-Res"]
                }
            ],
            "recommended_actions": [
                "impression", "play", "play_end", "pause",
                "like", "add_playlist", "share", "repeat"
            ]
        },
        "tags": ["music", "audio", "streaming"],
        "industries": ["音乐", "娱乐"]
    },
    
    "education": {
        "template_id": "education_default",
        "scenario_type": "education",
        "name": "在线教育场景标准模板",
        "description": "适用于在线课程、学习资源推荐等场景",
        "config": {
            "required_fields": [
                {
                    "field_name": "lesson_duration",
                    "field_type": "integer",
                    "required": True,
                    "description": "课时时长（秒）",
                    "min_value": 1
                },
                {
                    "field_name": "study_duration",
                    "field_type": "integer",
                    "required": True,
                    "description": "学习时长（秒）",
                    "min_value": 0
                },
                {
                    "field_name": "progress",
                    "field_type": "float",
                    "required": True,
                    "description": "学习进度（0-1）",
                    "min_value": 0.0,
                    "max_value": 1.0
                }
            ],
            "optional_fields": [
                {
                    "field_name": "course_id",
                    "field_type": "string",
                    "required": False,
                    "description": "课程ID"
                },
                {
                    "field_name": "score",
                    "field_type": "float",
                    "required": False,
                    "description": "得分",
                    "min_value": 0.0,
                    "max_value": 100.0
                },
                {
                    "field_name": "difficulty_level",
                    "field_type": "string",
                    "required": False,
                    "description": "难度等级",
                    "enum_values": ["初级", "中级", "高级", "专家"]
                }
            ],
            "recommended_actions": [
                "impression", "click", "learn", "complete",
                "pause", "trial", "note", "ask", "purchase"
            ]
        },
        "tags": ["education", "e-learning", "course"],
        "industries": ["教育", "培训"]
    }
}

