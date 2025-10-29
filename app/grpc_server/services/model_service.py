"""模型管理 gRPC 服务实现"""
import sys
from pathlib import Path

grpc_gen_path = Path(__file__).parent.parent.parent / "grpc_generated" / "python"
sys.path.insert(0, str(grpc_gen_path))

import grpc
from google.protobuf.json_format import MessageToDict
from recommender.v1 import model_pb2, model_pb2_grpc
from recommender_common.v1 import common_pb2
from loguru import logger

from app.services.model import ModelService
from app.models.model import ModelCreate, ModelUpdate, ModelType, ModelStatus, TrainModelRequest, DeployModelRequest
from app.models.base import PaginationParams
from .base_service import BaseServicer


class ModelServicer(model_pb2_grpc.ModelServiceServicer, BaseServicer):
    """模型管理 gRPC 服务"""
    
    def __init__(self, db):
        self.db = db
        self.model_service = ModelService(db)
    
    async def CreateModel(self, request, context):
        """创建模型"""
        try:
            logger.info(f"创建模型: tenant_id={request.tenant_id}, model_id={request.model_id}")
            
            # 转换模型类型枚举
            model_type_map = {
                model_pb2.MODEL_TYPE_RECALL: ModelType.RECALL,
                model_pb2.MODEL_TYPE_RANK: ModelType.RANK,
                model_pb2.MODEL_TYPE_RERANK: ModelType.RERANK,
            }
            model_type = model_type_map.get(request.model_type, ModelType.RANK)
            
            # 构造创建请求
            config_dict = MessageToDict(request.config) if request.config else {}
            
            model_create = ModelCreate(
                tenant_id=request.tenant_id,
                model_id=request.model_id,
                name=request.name,
                model_type=model_type,
                algorithm=request.algorithm,
                version=request.version if request.version else "v1.0",
                description=None,  # description 字段不在 CreateModelRequest 中
                config=config_dict
            )
            
            result = await self.model_service.create_model(
                tenant_id=request.tenant_id,
                data=model_create
            )
            
            response = model_pb2.CreateModelResponse()
            self._dict_to_model_proto(result.model_dump(), response.model)
            
            logger.info(f"模型创建成功: {request.model_id}")
            return response
            
        except ValueError as e:
            logger.error(f"创建模型失败(参数错误): {e}")
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(str(e))
            raise
        except Exception as e:
            logger.error(f"创建模型失败: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def GetModel(self, request, context):
        """获取模型详情"""
        try:
            result = await self.model_service.get_model(
                tenant_id=request.tenant_id,
                model_id=request.model_id
            )
            
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("模型不存在")
                raise grpc.RpcError()
            
            response = model_pb2.GetModelResponse()
            self._dict_to_model_proto(result.model_dump(), response.model)
            return response
            
        except grpc.RpcError:
            raise
        except Exception as e:
            logger.error(f"获取模型失败: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def ListModels(self, request, context):
        """查询模型列表"""
        try:
            # 构造分页参数
            pagination = PaginationParams(
                page=request.page.page if request.page else 1,
                page_size=request.page.page_size if request.page else 20
            )
            
            # 转换模型类型枚举
            model_type = None
            if request.model_type and request.model_type != model_pb2.MODEL_TYPE_UNSPECIFIED:
                model_type_map = {
                    model_pb2.MODEL_TYPE_RECALL: ModelType.RECALL,
                    model_pb2.MODEL_TYPE_RANK: ModelType.RANK,
                    model_pb2.MODEL_TYPE_RERANK: ModelType.RERANK,
                }
                model_type = model_type_map.get(request.model_type)
            
            # 转换模型状态枚举
            status = None
            if request.status:
                status_map = {
                    "draft": ModelStatus.DRAFT,
                    "training": ModelStatus.TRAINING,
                    "trained": ModelStatus.TRAINED,
                    "deployed": ModelStatus.DEPLOYED,
                    "failed": ModelStatus.FAILED,
                    "archived": ModelStatus.ARCHIVED,
                }
                status = status_map.get(request.status)
            
            # 查询列表
            models, total = await self.model_service.list_models(
                tenant_id=request.tenant_id if request.tenant_id else None,
                model_type=model_type,
                status=status,
                pagination=pagination
            )
            
            logger.info(f"查询到 {len(models)} 条模型, 总数: {total}")
            
            # 构造响应
            response = model_pb2.ListModelsResponse()
            for model in models:
                model_proto = response.models.add()
                self._dict_to_model_proto(model.model_dump(), model_proto)
            
            # 设置分页信息
            response.page_info.page = pagination.page
            response.page_info.page_size = pagination.page_size
            response.page_info.total = total
            response.page_info.total_pages = (total + pagination.page_size - 1) // pagination.page_size
            
            return response
            
        except Exception as e:
            logger.error(f"查询模型列表失败: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def UpdateModel(self, request, context):
        """更新模型"""
        try:
            # 构造更新请求
            config_dict = MessageToDict(request.config) if request.config else None
            
            model_update = ModelUpdate(
                name=request.name if request.name else None,
                description=request.description if request.description else None,
                config=config_dict
            )
            
            result = await self.model_service.update_model(
                tenant_id=request.tenant_id,
                model_id=request.model_id,
                data=model_update
            )
            
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("模型不存在")
                raise grpc.RpcError()
            
            response = model_pb2.UpdateModelResponse()
            self._dict_to_model_proto(result.model_dump(), response.model)
            return response
            
        except grpc.RpcError:
            raise
        except Exception as e:
            logger.error(f"更新模型失败: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def DeleteModel(self, request, context):
        """删除模型"""
        try:
            success = await self.model_service.delete_model(
                tenant_id=request.tenant_id,
                model_id=request.model_id
            )
            
            response = model_pb2.DeleteModelResponse()
            response.success = success
            return response
            
        except Exception as e:
            logger.error(f"删除模型失败: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def TrainModel(self, request, context):
        """训练模型"""
        try:
            train_request = TrainModelRequest(
                training_config=MessageToDict(request.training_config) if request.training_config else {}
            )
            
            result = await self.model_service.train_model(
                tenant_id=request.tenant_id,
                model_id=request.model_id,
                request=train_request
            )
            
            response = model_pb2.TrainModelResponse()
            self._dict_to_model_proto(result.model_dump(), response.model)
            return response
            
        except Exception as e:
            logger.error(f"训练模型失败: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def GetTrainingStatus(self, request, context):
        """获取训练状态"""
        try:
            status_dict = await self.model_service.get_training_status(
                tenant_id=request.tenant_id,
                model_id=request.model_id
            )
            
            response = model_pb2.GetTrainingStatusResponse()
            response.training_status = status_dict.get("training_status", "not_started")
            response.training_progress = status_dict.get("training_progress", 0.0)
            # metrics 和 log 可以根据需要添加
            
            return response
            
        except Exception as e:
            logger.error(f"获取训练状态失败: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def DeployModel(self, request, context):
        """部署模型"""
        try:
            deploy_request = DeployModelRequest(
                deployment_config=MessageToDict(request.deployment_config) if request.deployment_config else {}
            )
            
            result = await self.model_service.deploy_model(
                tenant_id=request.tenant_id,
                model_id=request.model_id,
                request=deploy_request
            )
            
            response = model_pb2.DeployModelResponse()
            self._dict_to_model_proto(result.model_dump(), response.model)
            return response
            
        except Exception as e:
            logger.error(f"部署模型失败: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    def _dict_to_model_proto(self, data: dict, model_proto):
        """将字典转换为 Model protobuf 消息"""
        try:
            # 基本字段
            if "tenant_id" in data:
                model_proto.tenant_id = data["tenant_id"]
            if "model_id" in data:
                model_proto.model_id = data["model_id"]
            if "name" in data:
                model_proto.name = data["name"]
            if "algorithm" in data:
                model_proto.algorithm = data["algorithm"]
            if "version" in data:
                model_proto.version = data["version"]
            if "description" in data and data["description"]:
                model_proto.description = data["description"]
            
            # 模型类型枚举
            if "model_type" in data:
                type_map = {
                    "recall": model_pb2.MODEL_TYPE_RECALL,
                    "rank": model_pb2.MODEL_TYPE_RANK,
                    "rerank": model_pb2.MODEL_TYPE_RERANK,
                }
                model_proto.model_type = type_map.get(data["model_type"], model_pb2.MODEL_TYPE_UNSPECIFIED)
            
            # 状态
            if "status" in data:
                model_proto.status = data["status"]
            if "training_status" in data:
                model_proto.training_status = data["training_status"]
            if "training_progress" in data:
                model_proto.training_progress = data["training_progress"]
            
            # 时间戳
            if "created_at" in data and data["created_at"]:
                model_proto.created_at.FromDatetime(data["created_at"])
            if "updated_at" in data and data["updated_at"]:
                model_proto.updated_at.FromDatetime(data["updated_at"])
            if "deployed_at" in data and data["deployed_at"]:
                model_proto.deployed_at.FromDatetime(data["deployed_at"])
            
        except Exception as e:
            logger.error(f"转换模型protobuf失败: {e}")
            raise

