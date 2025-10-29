"""数据集数据模型"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DatasetBase(BaseModel):
    """数据集基础模型"""
    name: str
    description: Optional[str] = ""
    storage_type: str  # "oss" or "s3"
    path: str
    file_size: int
    format: str  # "csv", "parquet", "json"
    row_count: Optional[int] = None


class Dataset(DatasetBase):
    """数据集完整模型"""
    dataset_id: str
    tenant_id: str
    created_by: str
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class DatasetCreate(DatasetBase):
    """创建数据集请求模型"""
    tenant_id: str
    created_by: str


class DatasetUpdate(BaseModel):
    """更新数据集请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    row_count: Optional[int] = None

