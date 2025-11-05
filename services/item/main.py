# -*- coding: utf-8 -*-
"""
物品服务 - gRPC实现
职责：物品CRUD、搜索、向量管理
"""
import sys
import os
import asyncio
from datetime import datetime
from typing import Optional, List
from concurrent import futures

import grpc
from motor.motor_asyncio import AsyncIOMotorClient
from google.protobuf import struct_pb2, timestamp_pb2

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.config import settings
from app.core.service_config import ServiceConfig
from app.grpc_generated.python.recommender.v1 import item_pb2
from app.grpc_generated.python.recommender.v1 import item_pb2_grpc


class ItemService:
    """物品服务核心逻辑"""
    
    def __init__(self, db):
        self.db = db
        self.items = db.items
        print("[ItemService] 初始化完成")
    
    async def create_item(self, tenant_id: str, scenario_id: str, item_id: str, 
                          metadata: dict, embedding: List[float] = None) -> Optional[dict]:
        """创建物品"""
        try:
            item_doc = {
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "item_id": item_id,
                "metadata": metadata,
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            if embedding:
                item_doc["embedding"] = embedding
            
            result = await self.items.insert_one(item_doc)
            item_doc["_id"] = result.inserted_id
            print(f"[ItemService] 创建物品: {item_id}")
            return item_doc
        except Exception as e:
            print(f"[ItemService] 创建物品失败: {e}")
            return None
    
    async def get_item(self, tenant_id: str, scenario_id: str, item_id: str) -> Optional[dict]:
        """获取物品"""
        try:
            item = await self.items.find_one({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "item_id": item_id
            })
            return item
        except Exception as e:
            print(f"[ItemService] 获取物品失败: {e}")
            return None
    
    async def update_item(self, tenant_id: str, scenario_id: str, item_id: str,
                         metadata: dict = None, embedding: List[float] = None, 
                         status: str = None) -> Optional[dict]:
        """更新物品"""
        try:
            update_fields = {"updated_at": datetime.utcnow()}
            if metadata:
                update_fields["metadata"] = metadata
            if embedding:
                update_fields["embedding"] = embedding
            if status:
                update_fields["status"] = status
            
            item = await self.items.find_one_and_update(
                {"tenant_id": tenant_id, "scenario_id": scenario_id, "item_id": item_id},
                {"$set": update_fields},
                return_document=True
            )
            return item
        except Exception as e:
            print(f"[ItemService] 更新物品失败: {e}")
            return None
    
    async def delete_item(self, tenant_id: str, scenario_id: str, item_id: str) -> bool:
        """删除物品"""
        try:
            result = await self.items.delete_one({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "item_id": item_id
            })
            return result.deleted_count > 0
        except Exception as e:
            print(f"[ItemService] 删除物品失败: {e}")
            return False


def _convert_item_to_pb(item: dict) -> item_pb2.Item:
    """转换物品为protobuf消息"""
    pb_item = item_pb2.Item(
        id=str(item.get("_id", "")),
        tenant_id=item.get("tenant_id", ""),
        scenario_id=item.get("scenario_id", ""),
        item_id=item.get("item_id", ""),
        status=item.get("status", "active")
    )
    
    if "metadata" in item:
        pb_item.metadata.update(item["metadata"])
    
    if "embedding" in item:
        pb_item.embedding.extend(item["embedding"])
    
    if "created_at" in item:
        ts = timestamp_pb2.Timestamp()
        ts.FromDatetime(item["created_at"])
        pb_item.created_at.CopyFrom(ts)
    
    if "updated_at" in item:
        ts = timestamp_pb2.Timestamp()
        ts.FromDatetime(item["updated_at"])
        pb_item.updated_at.CopyFrom(ts)
    
    return pb_item


class ItemServicer(item_pb2_grpc.ItemServiceServicer):
    """物品服务gRPC实现"""
    
    def __init__(self, item_service: ItemService):
        self.item_service = item_service
    
    async def CreateItem(self, request, context):
        """创建物品"""
        try:
            metadata = dict(request.metadata) if request.metadata else {}
            embedding = list(request.embedding) if request.embedding else None
            
            item = await self.item_service.create_item(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                item_id=request.item_id,
                metadata=metadata,
                embedding=embedding
            )
            
            if item:
                return item_pb2.CreateItemResponse(item=_convert_item_to_pb(item))
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Failed to create item")
                return item_pb2.CreateItemResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Create item failed: {str(e)}")
            return item_pb2.CreateItemResponse()
    
    async def GetItem(self, request, context):
        """获取物品"""
        try:
            item = await self.item_service.get_item(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                item_id=request.item_id
            )
            
            if item:
                return item_pb2.GetItemResponse(item=_convert_item_to_pb(item))
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Item not found")
                return item_pb2.GetItemResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Get item failed: {str(e)}")
            return item_pb2.GetItemResponse()
    
    async def UpdateItem(self, request, context):
        """更新物品"""
        try:
            metadata = dict(request.metadata) if request.metadata else None
            embedding = list(request.embedding) if request.embedding else None
            status = request.status if request.status else None
            
            item = await self.item_service.update_item(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                item_id=request.item_id,
                metadata=metadata,
                embedding=embedding,
                status=status
            )
            
            if item:
                return item_pb2.UpdateItemResponse(item=_convert_item_to_pb(item))
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Item not found")
                return item_pb2.UpdateItemResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Update item failed: {str(e)}")
            return item_pb2.UpdateItemResponse()
    
    async def DeleteItem(self, request, context):
        """删除物品"""
        try:
            success = await self.item_service.delete_item(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                item_id=request.item_id
            )
            return item_pb2.DeleteItemResponse(success=success)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Delete item failed: {str(e)}")
            return item_pb2.DeleteItemResponse(success=False)


async def serve():
    """启动gRPC服务"""
    config = ServiceConfig()
    host = os.getenv("GRPC_HOST", "0.0.0.0")
    port = int(os.getenv("GRPC_PORT", "8085"))
    
    mongo_url = config.get_mongodb_url()
    mongo_client = AsyncIOMotorClient(mongo_url)
    db = mongo_client[config.mongodb_database]
    
    item_service = ItemService(db)
    
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )
    
    item_pb2_grpc.add_ItemServiceServicer_to_server(
        ItemServicer(item_service),
        server
    )
    
    server.add_insecure_port(f"{host}:{port}")
    await server.start()
    
    print(f"[ItemService] gRPC服务启动于 {host}:{port}")
    print(f"[ItemService] MongoDB: {config.mongodb_host}")
    
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
