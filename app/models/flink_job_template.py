"""
Flink 作业模板模型
支持动态配置作业类型和参数，不限于固定的3种作业
"""
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from app.models.base import MongoBaseModel


class JobStatus(str, Enum):
    """作业状态"""
    CREATED = "created"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    RECONCILING = "reconciling"


class JobTemplateType(str, Enum):
    """作业模板类型"""
    PYTHON_SCRIPT = "python_script"  # Python 脚本
    JAR = "jar"  # Flink JAR
    SQL = "sql"  # Flink SQL
    PYTHON_FLINK = "python_flink"  # PyFlink


class JobTemplate(MongoBaseModel):
    """
    Flink 作业模板（存储在 MongoDB）
    
    支持动态配置任意作业类型，不限于固定的3种
    """
    
    template_id: str = Field(..., description="模板ID（全局唯一）")
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    
    # 作业类型
    job_type: JobTemplateType = Field(..., description="作业类型")
    
    # 作业配置（根据 job_type 不同而不同）
    # Python Script: {"script_path": "...", "entry_point": "...", "args": [...]}
    # JAR: {"jar_path": "...", "main_class": "...", "args": [...]}
    # SQL: {"sql_file": "..."}
    # PyFlink: {"module": "...", "function": "...", "args": [...]}
    config: Dict[str, Any] = Field(..., description="作业配置（根据类型动态）")
    
    # 执行环境配置
    parallelism: int = Field(default=1, description="并行度")
    checkpoints_enabled: bool = Field(default=True, description="是否启用检查点")
    checkpoint_interval_ms: int = Field(default=60000, description="检查点间隔（毫秒）")
    savepoint_path: Optional[str] = Field(None, description="Savepoint 路径")
    
    # 资源配置
    task_manager_memory: str = Field(default="1024m", description="TaskManager 内存")
    job_manager_memory: str = Field(default="512m", description="JobManager 内存")
    
    # 状态
    status: str = Field(default="active", description="模板状态：active, inactive")
    
    # 元数据
    tags: List[str] = Field(default_factory=list, description="标签")
    created_by: Optional[str] = Field(None, description="创建者")
    
    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "hot_score_v1",
                "name": "物品热度计算",
                "description": "实时计算物品热度分数",
                "job_type": "python_script",
                "config": {
                    "script_path": "flink_jobs/item_hot_score_calculator.py",
                    "entry_point": "main",
                    "args": []
                },
                "parallelism": 4,
                "checkpoints_enabled": True,
                "checkpoint_interval_ms": 60000
            }
        }


class FlinkJob(MongoBaseModel):
    """
    Flink 作业实例（存储在 MongoDB）
    
    记录提交到 Flink 集群的作业信息
    """
    
    job_id: str = Field(..., description="作业ID（全局唯一，对应 Flink Job ID）")
    job_name: str = Field(..., description="作业名称")
    
    # 关联模板
    template_id: str = Field(..., description="关联的模板ID")
    
    # Flink 集群信息
    flink_job_id: Optional[str] = Field(None, description="Flink 集群返回的 Job ID")
    flink_cluster_url: str = Field(..., description="Flink 集群 REST URL")
    
    # 作业状态
    status: JobStatus = Field(default=JobStatus.CREATED, description="作业状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 作业配置（提交时的快照）
    job_config: Dict[str, Any] = Field(..., description="作业配置快照")
    
    # 提交信息
    submitted_by: Optional[str] = Field(None, description="提交者")
    submitted_at: Optional[str] = Field(None, description="提交时间")
    
    # 运行信息
    start_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")
    duration: Optional[int] = Field(None, description="运行时长（秒）")
    
    # 统计信息
    num_operators: Optional[int] = Field(None, description="算子数量")
    num_vertices: Optional[int] = Field(None, description="顶点数量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "hot_score_tenant_001_video_recommendation",
                "job_name": "物品热度计算 - tenant_001/video_recommendation",
                "template_id": "hot_score_v1",
                "flink_cluster_url": "http://localhost:8081",
                "status": "running",
                "job_config": {
                    "tenant_id": "tenant_001",
                    "scenario_id": "video_recommendation",
                    "parallelism": 4
                }
            }
        }


class JobTemplateCreate(BaseModel):
    """创建作业模板请求"""
    template_id: str
    name: str
    description: Optional[str] = None
    job_type: JobTemplateType
    config: Dict[str, Any]
    parallelism: int = 1
    checkpoints_enabled: bool = True
    checkpoint_interval_ms: int = 60000
    task_manager_memory: str = "1024m"
    job_manager_memory: str = "512m"
    tags: List[str] = Field(default_factory=list)


class FlinkJobSubmitRequest(BaseModel):
    """提交 Flink 作业请求"""
    template_id: str
    job_id: str
    job_name: str
    job_config: Dict[str, Any] = Field(default_factory=dict)  # 运行时参数覆盖模板配置
    flink_cluster_url: Optional[str] = None  # 如果不指定，使用默认配置
    savepoint_path: Optional[str] = None  # 从 Savepoint 恢复


class FlinkJobControlRequest(BaseModel):
    """Flink 作业控制请求"""
    job_id: str
    flink_cluster_url: Optional[str] = None  # 如果不指定，使用默认配置

