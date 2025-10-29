"""
AB实验数据模型
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class ExperimentStatus(str, Enum):
    """实验状态"""
    DRAFT = "draft"  # 草稿
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 暂停
    COMPLETED = "completed"  # 已完成
    ARCHIVED = "archived"  # 已归档


class TrafficSplitMethod(str, Enum):
    """流量分配方法"""
    USER_ID_HASH = "user_id_hash"  # 基于用户ID哈希
    RANDOM = "random"  # 随机分配
    WEIGHTED = "weighted"  # 加权分配


class ExperimentVariant(BaseModel):
    """实验变体（实验组/对照组）"""
    variant_id: str = Field(..., description="变体ID")
    name: str = Field(..., description="变体名称")
    description: str = Field(default="", description="变体描述")
    traffic_percentage: float = Field(..., ge=0, le=100, description="流量占比（0-100）")
    config: Dict[str, Any] = Field(default_factory=dict, description="变体配置")
    
    # 策略配置
    recall_strategy: Optional[Dict[str, Any]] = Field(None, description="召回策略配置")
    rank_model: Optional[str] = Field(None, description="排序模型")
    rerank_rules: Optional[List[str]] = Field(None, description="重排规则")


class ExperimentMetrics(BaseModel):
    """实验指标"""
    # 主要指标
    primary_metric: str = Field(..., description="主要指标（如CTR）")
    
    # 次要指标
    secondary_metrics: List[str] = Field(
        default_factory=list,
        description="次要指标（如转化率、观看时长）"
    )
    
    # 护栏指标（不能恶化）
    guardrail_metrics: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="护栏指标 [{name, threshold, direction}]"
    )


class Experiment(BaseModel):
    """AB实验"""
    experiment_id: str = Field(..., description="实验ID")
    tenant_id: str = Field(..., description="租户ID")
    scenario_id: str = Field(..., description="场景ID")
    
    # 基本信息
    name: str = Field(..., description="实验名称")
    description: str = Field(default="", description="实验描述")
    hypothesis: str = Field(default="", description="实验假设")
    
    # 状态
    status: ExperimentStatus = Field(
        default=ExperimentStatus.DRAFT,
        description="实验状态"
    )
    
    # 时间
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    
    # 流量配置
    traffic_split_method: TrafficSplitMethod = Field(
        default=TrafficSplitMethod.USER_ID_HASH,
        description="流量分配方法"
    )
    variants: List[ExperimentVariant] = Field(..., description="实验变体列表")
    
    # 目标用户
    target_users: Optional[Dict[str, Any]] = Field(
        None,
        description="目标用户过滤条件 {user_segment, user_tags, ...}"
    )
    
    # 指标配置
    metrics: ExperimentMetrics = Field(..., description="实验指标")
    
    # 统计配置
    min_sample_size: int = Field(default=1000, description="最小样本量")
    confidence_level: float = Field(default=0.95, description="置信水平")
    
    # 创建者
    created_by: str = Field(default="system", description="创建者")
    
    class Config:
        json_schema_extra = {
            "example": {
                "experiment_id": "exp_001",
                "tenant_id": "demo_tenant",
                "scenario_id": "vlog_main_feed",
                "name": "新召回策略实验",
                "description": "测试基于向量的召回策略效果",
                "hypothesis": "向量召回能提升CTR 5%",
                "status": "running",
                "traffic_split_method": "user_id_hash",
                "variants": [
                    {
                        "variant_id": "control",
                        "name": "对照组",
                        "traffic_percentage": 50,
                        "config": {},
                        "recall_strategy": {"collaborative_filtering": {"weight": 0.5}}
                    },
                    {
                        "variant_id": "treatment",
                        "name": "实验组",
                        "traffic_percentage": 50,
                        "config": {},
                        "recall_strategy": {"vector_search": {"weight": 0.7}}
                    }
                ],
                "metrics": {
                    "primary_metric": "ctr",
                    "secondary_metrics": ["avg_watch_duration", "engagement_rate"],
                    "guardrail_metrics": [
                        {"name": "coverage", "threshold": 0.5, "direction": ">="}
                    ]
                },
                "created_by": "admin@example.com"
            }
        }


class ExperimentAssignment(BaseModel):
    """实验分配记录"""
    tenant_id: str
    experiment_id: str
    user_id: str
    variant_id: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)


class ExperimentResult(BaseModel):
    """实验结果"""
    experiment_id: str
    variant_id: str
    
    # 样本统计
    sample_size: int = Field(..., description="样本量")
    
    # 指标结果
    metrics: Dict[str, float] = Field(..., description="指标结果")
    
    # 统计显著性
    is_significant: bool = Field(..., description="是否显著")
    p_value: float = Field(..., description="P值")
    confidence_interval: List[float] = Field(..., description="置信区间")
    
    # 对比基线的提升
    lift: Dict[str, float] = Field(..., description="相对对照组的提升 {metric: lift%}")
    
    # 计算时间
    computed_at: datetime = Field(default_factory=datetime.utcnow)

