"""物品管理 gRPC 服务实现"""
import sys
from pathlib import Path

grpc_gen_path = Path(__file__).parent.parent.parent / "grpc_generated" / "python"
sys.path.insert(0, str(grpc_gen_path))

import grpc
from recommender.v1 import item_pb2, item_pb2_grpc
from app.services.item.service import ItemService
from .base_service import BaseServicer


class ItemServicer(item_pb2_grpc.ItemServiceServicer, BaseServicer):
    """物品管理 gRPC 服务"""
    
    def __init__(self):
        self.item_service = ItemService()
    
    async def CreateItem(self, request, context) -> item_pb2.CreateItemResponse:
        """创建物品"""
        try:
            metadata = self._struct_to_dict(request.metadata) if request.metadata else {}
            
            item_data = {
                "tenant_id": request.tenant_id,
                "scenario_id": request.scenario_id,
                "item_id": request.item_id,
                "metadata": metadata,
                "embedding": list(request.embedding) if request.embedding else None,
            }
            
            result = await self.item_service.create_item(item_data)
            
            response = item_pb2.CreateItemResponse()
            self._dict_to_item_proto(result, response.item)
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"创建物品失败: {str(e)}")
            raise
    
    async def BatchCreateItems(self, request, context) -> item_pb2.BatchCreateItemsResponse:
        """批量创建物品"""
        try:
            items_data = []
            for item_input in request.items:
                metadata = self._struct_to_dict(item_input.metadata) if item_input.metadata else {}
                items_data.append({
                    "item_id": item_input.item_id,
                    "metadata": metadata,
                    "embedding": list(item_input.embedding) if item_input.embedding else None,
                })
            
            result = await self.item_service.batch_create_items(
                request.tenant_id,
                request.scenario_id,
                items_data
            )
            
            response = item_pb2.BatchCreateItemsResponse()
            for item in result.get("items", []):
                item_proto = response.items.add()
                self._dict_to_item_proto(item, item_proto)
            
            response.success_count = result.get("success_count", 0)
            response.failed_count = result.get("failed_count", 0)
            response.errors.extend(result.get("errors", []))
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"批量创建物品失败: {str(e)}")
            raise
    
    async def GetItem(self, request, context) -> item_pb2.GetItemResponse:
        """获取物品详情"""
        try:
            result = await self.item_service.get_item(
                request.tenant_id,
                request.scenario_id,
                request.item_id
            )
            
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("物品不存在")
                raise grpc.RpcError()
            
            response = item_pb2.GetItemResponse()
            self._dict_to_item_proto(result, response.item)
            return response
            
        except grpc.RpcError:
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"获取物品失败: {str(e)}")
            raise
    
    async def ListItems(self, request, context) -> item_pb2.ListItemsResponse:
        """查询物品列表"""
        try:
            filters = {
                "tenant_id": request.tenant_id,
                "scenario_id": request.scenario_id,
            }
            if request.status:
                filters["status"] = request.status
            
            page = request.page.page if request.HasField("page") else 1
            page_size = request.page.page_size if request.HasField("page") else 20
            
            result = await self.item_service.list_items(
                filters=filters,
                page=page,
                page_size=page_size
            )
            
            response = item_pb2.ListItemsResponse()
            for item in result.get("items", []):
                item_proto = response.items.add()
                self._dict_to_item_proto(item, item_proto)
            
            if "page_info" in result:
                self._set_page_info(result["page_info"], response.page_info)
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"查询物品列表失败: {str(e)}")
            raise
    
    async def UpdateItem(self, request, context) -> item_pb2.UpdateItemResponse:
        """更新物品"""
        try:
            update_data = {}
            if request.metadata:
                update_data["metadata"] = self._struct_to_dict(request.metadata)
            if request.embedding:
                update_data["embedding"] = list(request.embedding)
            if request.status:
                update_data["status"] = request.status
            
            result = await self.item_service.update_item(
                request.tenant_id,
                request.scenario_id,
                request.item_id,
                update_data
            )
            
            response = item_pb2.UpdateItemResponse()
            self._dict_to_item_proto(result, response.item)
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"更新物品失败: {str(e)}")
            raise
    
    async def DeleteItem(self, request, context) -> item_pb2.DeleteItemResponse:
        """删除物品"""
        try:
            await self.item_service.delete_item(
                request.tenant_id,
                request.scenario_id,
                request.item_id
            )
            return item_pb2.DeleteItemResponse(success=True)
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"删除物品失败: {str(e)}")
            raise
    
    async def BatchDeleteItems(self, request, context) -> item_pb2.BatchDeleteItemsResponse:
        """批量删除物品"""
        try:
            result = await self.item_service.batch_delete_items(
                request.tenant_id,
                request.scenario_id,
                list(request.item_ids)
            )
            
            response = item_pb2.BatchDeleteItemsResponse()
            response.success_count = result.get("success_count", 0)
            response.failed_count = result.get("failed_count", 0)
            response.errors.extend(result.get("errors", []))
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"批量删除物品失败: {str(e)}")
            raise
    
    async def SearchItems(self, request, context) -> item_pb2.SearchItemsResponse:
        """搜索物品"""
        try:
            filters = self._struct_to_dict(request.filters) if request.filters else {}
            
            page = request.page.page if request.HasField("page") else 1
            page_size = request.page.page_size if request.HasField("page") else 20
            
            result = await self.item_service.search_items(
                request.tenant_id,
                request.scenario_id,
                request.query,
                filters=filters,
                page=page,
                page_size=page_size
            )
            
            response = item_pb2.SearchItemsResponse()
            for item in result.get("items", []):
                item_proto = response.items.add()
                self._dict_to_item_proto(item, item_proto)
            
            if "page_info" in result:
                self._set_page_info(result["page_info"], response.page_info)
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"搜索物品失败: {str(e)}")
            raise
    
    def _dict_to_item_proto(self, data: dict, item: item_pb2.Item):
        """将 dict 转换为 Item proto message"""
        item.id = str(data.get("_id", ""))
        item.tenant_id = data.get("tenant_id", "")
        item.scenario_id = data.get("scenario_id", "")
        item.item_id = data.get("item_id", "")
        item.status = data.get("status", "active")
        
        if "metadata" in data and data["metadata"]:
            self._dict_to_struct(data["metadata"], item.metadata)
        
        if "embedding" in data and data["embedding"]:
            item.embedding.extend(data["embedding"])
        
        if "created_at" in data and data["created_at"]:
            self._datetime_to_timestamp(data["created_at"], item.created_at)
        if "updated_at" in data and data["updated_at"]:
            self._datetime_to_timestamp(data["updated_at"], item.updated_at)

