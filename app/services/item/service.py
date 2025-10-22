"""
物品管理服务
"""
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from app.models.item import (
    Item,
    ItemCreate,
    ItemUpdate,
    ItemStatus,
    ItemListQuery
)
from app.models.base import PaginationParams


class ItemService:
    """物品管理服务"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.items
    
    async def create_item(
        self,
        tenant_id: str,
        data: ItemCreate
    ) -> Item:
        """创建物品"""
        
        # 检查item_id是否已存在
        existing = await self.collection.find_one({
            "tenant_id": tenant_id,
            "scenario_id": data.scenario_id,
            "item_id": data.item_id
        })
        if existing:
            raise ValueError(f"物品ID已存在: {data.item_id}")
        
        # 创建物品文档
        item_dict = {
            "tenant_id": tenant_id,
            **data.model_dump(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.collection.insert_one(item_dict)
        item_dict["_id"] = result.inserted_id
        
        return Item(**item_dict)
    
    async def batch_create_items(
        self,
        tenant_id: str,
        scenario_id: str,
        items: List[Dict[str, Any]]
    ) -> int:
        """批量创建物品"""
        
        if not items:
            return 0
        
        # 准备批量插入数据
        now = datetime.utcnow()
        documents = []
        
        for item_data in items:
            # 确保必填字段
            if "item_id" not in item_data:
                continue
                
            doc = {
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "item_id": item_data["item_id"],
                "metadata": item_data.get("metadata", {}),
                "embedding": item_data.get("embedding"),
                "status": item_data.get("status", ItemStatus.ACTIVE),
                "created_at": now,
                "updated_at": now
            }
            documents.append(doc)
        
        if not documents:
            return 0
        
        # 批量插入（忽略重复的item_id）
        try:
            result = await self.collection.insert_many(
                documents,
                ordered=False  # 继续插入即使有些失败
            )
            return len(result.inserted_ids)
        except Exception as e:
            # 部分插入成功的情况
            if hasattr(e, 'details') and 'nInserted' in e.details:
                return e.details['nInserted']
            raise
    
    async def get_item(
        self,
        tenant_id: str,
        scenario_id: str,
        item_id: str
    ) -> Optional[Item]:
        """获取物品详情"""
        
        doc = await self.collection.find_one({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "item_id": item_id
        })
        
        if doc:
            return Item(**doc)
        return None
    
    async def list_items(
        self,
        tenant_id: str,
        query: Optional[ItemListQuery] = None,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[Item], int]:
        """查询物品列表"""
        
        # 构建查询条件
        filter_query = {"tenant_id": tenant_id}
        
        if query:
            if query.scenario_id:
                filter_query["scenario_id"] = query.scenario_id
            if query.status:
                filter_query["status"] = query.status
            if query.category:
                filter_query["metadata.category"] = query.category
        
        # 总数
        total = await self.collection.count_documents(filter_query)
        
        # 分页查询
        cursor = self.collection.find(filter_query).sort("created_at", -1)
        
        if pagination:
            cursor = cursor.skip(pagination.skip).limit(pagination.page_size)
        
        items = []
        async for doc in cursor:
            items.append(Item(**doc))
        
        return items, total
    
    async def update_item(
        self,
        tenant_id: str,
        scenario_id: str,
        item_id: str,
        data: ItemUpdate
    ) -> Optional[Item]:
        """更新物品"""
        
        # 构建更新字段
        update_data = {
            k: v for k, v in data.model_dump(exclude_unset=True).items()
            if v is not None
        }
        
        if not update_data:
            return await self.get_item(tenant_id, scenario_id, item_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        # 执行更新
        result = await self.collection.find_one_and_update(
            {
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "item_id": item_id
            },
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            return Item(**result)
        return None
    
    async def delete_item(
        self,
        tenant_id: str,
        scenario_id: str,
        item_id: str,
        soft_delete: bool = True
    ) -> bool:
        """删除物品"""
        
        if soft_delete:
            # 软删除：更新状态为DELETED
            result = await self.collection.update_one(
                {
                    "tenant_id": tenant_id,
                    "scenario_id": scenario_id,
                    "item_id": item_id
                },
                {
                    "$set": {
                        "status": ItemStatus.DELETED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        else:
            # 硬删除：从数据库删除
            result = await self.collection.delete_one({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "item_id": item_id
            })
            return result.deleted_count > 0
    
    async def get_items_by_ids(
        self,
        tenant_id: str,
        scenario_id: str,
        item_ids: List[str]
    ) -> List[Item]:
        """批量获取物品"""
        
        if not item_ids:
            return []
        
        cursor = self.collection.find({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "item_id": {"$in": item_ids},
            "status": ItemStatus.ACTIVE
        })
        
        items = []
        async for doc in cursor:
            items.append(Item(**doc))
        
        return items
    
    async def search_items(
        self,
        tenant_id: str,
        scenario_id: str,
        search_text: str,
        limit: int = 20
    ) -> List[Item]:
        """搜索物品（简单文本搜索）"""
        
        # 在metadata中搜索
        cursor = self.collection.find({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "status": ItemStatus.ACTIVE,
            "$or": [
                {"metadata.title": {"$regex": search_text, "$options": "i"}},
                {"metadata.description": {"$regex": search_text, "$options": "i"}},
                {"metadata.tags": {"$regex": search_text, "$options": "i"}}
            ]
        }).limit(limit)
        
        items = []
        async for doc in cursor:
            items.append(Item(**doc))
        
        return items

