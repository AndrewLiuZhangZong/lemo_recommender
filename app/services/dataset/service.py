"""数据集服务实现"""
from typing import List, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.dataset import Dataset, DatasetCreate, DatasetUpdate
from app.models.base import PaginationParams


class DatasetService:
    """数据集管理服务"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["datasets"]
    
    async def create_dataset(self, dataset_data: DatasetCreate) -> Dataset:
        """创建数据集"""
        # 生成数据集ID
        dataset_id = str(ObjectId())
        
        # 构建数据集文档
        doc = {
            "dataset_id": dataset_id,
            "tenant_id": dataset_data.tenant_id,
            "name": dataset_data.name,
            "description": dataset_data.description or "",
            "storage_type": dataset_data.storage_type,
            "path": dataset_data.path,
            "file_size": dataset_data.file_size,
            "format": dataset_data.format,
            "row_count": dataset_data.row_count,
            "created_by": dataset_data.created_by,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        # 插入数据库
        await self.collection.insert_one(doc)
        
        return Dataset(**doc)
    
    async def get_dataset(self, tenant_id: str, dataset_id: str) -> Optional[Dataset]:
        """获取数据集详情"""
        doc = await self.collection.find_one({
            "tenant_id": tenant_id,
            "dataset_id": dataset_id
        })
        
        if not doc:
            return None
        
        try:
            return Dataset.model_validate(doc)
        except Exception as e:
            print(f"Error converting dataset document: {e}")
            return None
    
    async def list_datasets(
        self,
        tenant_id: str,
        pagination: PaginationParams,
        format_filter: Optional[str] = None
    ) -> Tuple[List[Dataset], int]:
        """获取数据集列表"""
        # 构建查询条件
        query = {"tenant_id": tenant_id}
        if format_filter:
            query["format"] = format_filter
        
        # 查询总数
        total = await self.collection.count_documents(query)
        
        # 分页查询
        skip = (pagination.page - 1) * pagination.page_size
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(pagination.page_size)
        
        # 转换为 Dataset 对象
        datasets = []
        async for doc in cursor:
            try:
                dataset = Dataset.model_validate(doc)
                datasets.append(dataset)
            except Exception as e:
                print(f"Error converting dataset document: {e}")
                continue
        
        return datasets, total
    
    async def update_dataset(
        self,
        tenant_id: str,
        dataset_id: str,
        update_data: DatasetUpdate
    ) -> Optional[Dataset]:
        """更新数据集"""
        # 构建更新数据
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            return await self.get_dataset(tenant_id, dataset_id)
        
        update_dict["updated_at"] = datetime.utcnow().isoformat()
        
        # 更新数据库
        result = await self.collection.find_one_and_update(
            {"tenant_id": tenant_id, "dataset_id": dataset_id},
            {"$set": update_dict},
            return_document=True
        )
        
        if not result:
            return None
        
        try:
            return Dataset.model_validate(result)
        except Exception as e:
            print(f"Error converting dataset document: {e}")
            return None
    
    async def delete_dataset(self, tenant_id: str, dataset_id: str) -> bool:
        """删除数据集"""
        result = await self.collection.delete_one({
            "tenant_id": tenant_id,
            "dataset_id": dataset_id
        })
        
        return result.deleted_count > 0

