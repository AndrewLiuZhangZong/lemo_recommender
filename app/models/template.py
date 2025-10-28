"""
配置模板模型
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

from app.models.base import MongoBaseModel


class Template(MongoBaseModel):
    """配置模板模型（MongoDB文档）"""
    
    template_id: str = Field(..., description="模板ID（唯一标识）")
    name: str = Field(..., description="模板名称")
    description: str = Field(default="", description="模板描述")
    scenario_types: List[str] = Field(default_factory=list, description="适用的场景类型列表")
    config: Dict[str, Any] = Field(default_factory=dict, description="配置内容")
    is_system: bool = Field(default=False, description="是否系统预设模板")
    creator: str = Field(default="", description="创建人")
    
    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "ecommerce_default",
                "name": "电商推荐模板",
                "description": "适用于电商场景的标准推荐配置",
                "scenario_types": ["ecommerce"],
                "config": {
                    "recall": {
                        "strategies": [
                            {"name": "user_cf", "weight": 0.3, "limit": 100}
                        ]
                    }
                },
                "is_system": True,
                "creator": "system"
            }
        }


# API请求/响应模型
class TemplateCreate(BaseModel):
    """创建模板请求"""
    template_id: str
    name: str
    description: Optional[str] = ""
    scenario_types: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    creator: Optional[str] = ""


class TemplateUpdate(BaseModel):
    """更新模板请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    scenario_types: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class TemplateResponse(BaseModel):
    """模板响应"""
    id: str
    template_id: str
    name: str
    description: str
    scenario_types: List[str]
    config: Dict[str, Any]
    is_system: bool
    creator: str
    created_at: str
    updated_at: str

