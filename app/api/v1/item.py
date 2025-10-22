"""
物品管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from app.core.database import get_mongodb
from app.api.dependencies import get_tenant_id
from app.models.item import (
    Item,
    ItemCreate,
    ItemUpdate,
    ItemBatchCreate,
    ItemResponse,
    ItemListQuery,
    ItemStatus
)
from app.models.base import PaginationParams, PaginatedResponse, ResponseModel
from app.services.item.service import ItemService


router = APIRouter()


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    data: ItemCreate,
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """创建物品"""
    
    service = ItemService(db)
    
    try:
        item = await service.create_item(tenant_id, data)
        return _to_response(item)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/batch", response_model=ResponseModel)
async def batch_create_items(
    data: ItemBatchCreate,
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """批量创建物品（支持API推送）"""
    
    service = ItemService(db)
    
    try:
        # 1. 写入MongoDB
        count = await service.batch_create_items(
            tenant_id=tenant_id,
            scenario_id=data.scenario_id,
            items=data.items
        )
        
        # 2. 触发后续处理（Kafka事件、向量生成等）
        from app.services.item.processor import ItemProcessor
        from app.core.kafka import KafkaProducer
        from app.core.config import settings
        
        kafka_producer = KafkaProducer(settings.kafka_bootstrap_servers)
        await kafka_producer.start()
        
        processor = ItemProcessor(kafka_producer)
        process_result = await processor.process_items(
            tenant_id=tenant_id,
            scenario_id=data.scenario_id,
            items=data.items,
            source="api"
        )
        
        await kafka_producer.stop()
        
        return ResponseModel(
            message=f"成功创建{count}个物品，后续处理已启动",
            data={
                "count": count,
                "processing": process_result
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=PaginatedResponse)
async def list_items(
    scenario_id: Optional[str] = Query(None),
    status_filter: Optional[ItemStatus] = Query(None, alias="status"),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """查询物品列表"""
    
    service = ItemService(db)
    
    query = ItemListQuery(
        scenario_id=scenario_id,
        status=status_filter,
        category=category
    )
    pagination = PaginationParams(page=page, page_size=page_size)
    
    items, total = await service.list_items(
        tenant_id=tenant_id,
        query=query,
        pagination=pagination
    )
    
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_response(item) for item in items]
    )


@router.get("/search", response_model=list[ItemResponse])
async def search_items(
    scenario_id: str = Query(...),
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100),
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """搜索物品"""
    
    service = ItemService(db)
    
    items = await service.search_items(
        tenant_id=tenant_id,
        scenario_id=scenario_id,
        search_text=q,
        limit=limit
    )
    
    return [_to_response(item) for item in items]


@router.get("/{scenario_id}/{item_id}", response_model=ItemResponse)
async def get_item(
    scenario_id: str,
    item_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """获取物品详情"""
    
    service = ItemService(db)
    item = await service.get_item(tenant_id, scenario_id, item_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"物品不存在: {item_id}"
        )
    
    return _to_response(item)


@router.put("/{scenario_id}/{item_id}", response_model=ItemResponse)
async def update_item(
    scenario_id: str,
    item_id: str,
    data: ItemUpdate,
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """更新物品"""
    
    service = ItemService(db)
    item = await service.update_item(tenant_id, scenario_id, item_id, data)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"物品不存在: {item_id}"
        )
    
    return _to_response(item)


@router.delete("/{scenario_id}/{item_id}", response_model=ResponseModel)
async def delete_item(
    scenario_id: str,
    item_id: str,
    hard_delete: bool = Query(False, description="是否硬删除"),
    tenant_id: str = Depends(get_tenant_id),
    db = Depends(get_mongodb)
):
    """删除物品"""
    
    service = ItemService(db)
    success = await service.delete_item(
        tenant_id=tenant_id,
        scenario_id=scenario_id,
        item_id=item_id,
        soft_delete=not hard_delete
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"物品不存在: {item_id}"
        )
    
    return ResponseModel(message="物品已删除")


def _to_response(item: Item) -> ItemResponse:
    """转换为响应模型"""
    return ItemResponse(
        id=str(item.id),
        tenant_id=item.tenant_id,
        scenario_id=item.scenario_id,
        item_id=item.item_id,
        metadata=item.metadata,
        status=item.status.value,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat()
    )

