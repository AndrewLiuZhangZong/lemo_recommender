"""推荐模型数据模型"""
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import Field
from .base import MongoBaseModel


class ModelType(str, Enum):
    """模型类型"""
    RECALL = "recall"      # 召回模型
    RANK = "rank"          # 排序模型
    RERANK = "rerank"      # 重排模型


class ModelStatus(str, Enum):
    """模型状态"""
    DRAFT = "draft"              # 草稿
    TRAINING = "training"        # 训练中
    TRAINED = "trained"          # 已训练
    DEPLOYED = "deployed"        # 已部署
    FAILED = "failed"            # 失败
    ARCHIVED = "archived"        # 已归档


class TrainingStatus(str, Enum):
    """训练状态"""
    NOT_STARTED = "not_started"  # 未开始
    RUNNING = "running"          # 运行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消


class Model(MongoBaseModel):
    """推荐模型"""
    tenant_id: str = Field(..., description="租户ID")
    scenario_id: str = Field(..., description="场景ID")
    model_id: str = Field(..., description="模型ID（租户+场景内唯一）")
    
    name: str = Field(..., description="模型名称")
    model_type: ModelType = Field(..., description="模型类型")
    algorithm: str = Field(..., description="算法名称（如 lightgbm, deepfm）")
    version: str = Field(default="v1.0", description="模型版本")
    
    description: Optional[str] = Field(None, description="模型描述")
    config: Dict[str, Any] = Field(default_factory=dict, description="模型配置")
    
    # 训练相关
    training_status: TrainingStatus = Field(
        default=TrainingStatus.NOT_STARTED, 
        description="训练状态"
    )
    training_progress: float = Field(default=0.0, description="训练进度 (0-100)")
    training_metrics: Dict[str, Any] = Field(default_factory=dict, description="训练指标")
    training_log: Optional[str] = Field(None, description="训练日志")
    
    # 部署相关
    status: ModelStatus = Field(default=ModelStatus.DRAFT, description="模型状态")
    deployed_at: Optional[datetime] = Field(None, description="部署时间")
    deployment_config: Dict[str, Any] = Field(default_factory=dict, description="部署配置")
    
    # 性能指标
    metrics: Dict[str, Any] = Field(default_factory=dict, description="评估指标")
    
    # 元数据
    creator: Optional[str] = Field(None, description="创建人")
    
    class Config:
        collection = "models"


class ModelCreate(MongoBaseModel):
    """创建模型请求"""
    tenant_id: str
    scenario_id: str
    model_id: str
    name: str
    model_type: ModelType
    algorithm: str
    version: str = "v1.0"
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class ModelUpdate(MongoBaseModel):
    """更新模型请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[ModelStatus] = None
    metrics: Optional[Dict[str, Any]] = None


class TrainModelRequest(MongoBaseModel):
    """训练模型请求"""
    training_config: Dict[str, Any] = Field(default_factory=dict, description="训练配置")


class DeployModelRequest(MongoBaseModel):
    """部署模型请求"""
    deployment_config: Dict[str, Any] = Field(default_factory=dict, description="部署配置")


class ModelResponse(Model):
    """模型响应"""
    pass

