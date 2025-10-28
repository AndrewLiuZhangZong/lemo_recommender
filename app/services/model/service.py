"""模型管理服务实现"""
from typing import List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from loguru import logger

from app.models.model import (
    Model, ModelCreate, ModelUpdate, ModelResponse,
    ModelType, ModelStatus, TrainingStatus,
    TrainModelRequest, DeployModelRequest
)
from app.models.base import PaginationParams


class ModelService:
    """模型管理服务"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.models
    
    async def create_model(
        self,
        tenant_id: str,
        data: ModelCreate
    ) -> ModelResponse:
        """创建模型"""
        try:
            # 检查模型ID是否已存在
            existing = await self.collection.find_one({
                "tenant_id": tenant_id,
                "scenario_id": data.scenario_id,
                "model_id": data.model_id
            })
            
            if existing:
                raise ValueError(f"模型ID {data.model_id} 已存在")
            
            # 创建模型文档
            model_dict = data.model_dump()
            model_dict["created_at"] = datetime.utcnow()
            model_dict["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(model_dict)
            
            # 返回创建的模型
            created_model = await self.collection.find_one({"_id": result.inserted_id})
            return Model.model_validate(created_model)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"创建模型失败: {e}")
            raise
    
    async def get_model(
        self,
        tenant_id: str,
        scenario_id: str,
        model_id: str
    ) -> Optional[ModelResponse]:
        """获取模型详情"""
        try:
            model_doc = await self.collection.find_one({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "model_id": model_id
            })
            
            if not model_doc:
                return None
            
            return Model.model_validate(model_doc)
        except Exception as e:
            logger.error(f"获取模型失败: {e}")
            raise
    
    async def list_models(
        self,
        tenant_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
        model_type: Optional[ModelType] = None,
        status: Optional[ModelStatus] = None,
        pagination: PaginationParams = PaginationParams()
    ) -> tuple[List[ModelResponse], int]:
        """查询模型列表"""
        try:
            # 构建查询条件
            query = {}
            if tenant_id and tenant_id.strip():
                query["tenant_id"] = tenant_id
            if scenario_id and scenario_id.strip():
                query["scenario_id"] = scenario_id
            if model_type:
                query["model_type"] = model_type
            if status:
                query["status"] = status
            
            logger.info(f"查询模型列表: query={query}, pagination={pagination}")
            
            # 查询总数
            total = await self.collection.count_documents(query)
            logger.info(f"符合条件的总数: {total}")
            
            # 分页查询
            skip = (pagination.page - 1) * pagination.page_size
            cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(pagination.page_size)
            
            # 转换为模型列表
            models: List[ModelResponse] = []
            async for doc in cursor:
                try:
                    model = Model.model_validate(doc)
                    models.append(model)
                except Exception as e:
                    logger.error(f"转换模型数据失败: {e}, doc={doc}")
                    continue
            
            logger.info(f"实际返回 {len(models)} 条数据")
            return models, total
        except Exception as e:
            logger.error(f"查询模型列表失败: {e}")
            raise
    
    async def update_model(
        self,
        tenant_id: str,
        scenario_id: str,
        model_id: str,
        data: ModelUpdate
    ) -> Optional[ModelResponse]:
        """更新模型"""
        try:
            # 构建更新数据（只更新非 None 的字段）
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            
            if not update_data:
                # 没有要更新的字段
                return await self.get_model(tenant_id, scenario_id, model_id)
            
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {
                    "tenant_id": tenant_id,
                    "scenario_id": scenario_id,
                    "model_id": model_id
                },
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                return None
            
            return await self.get_model(tenant_id, scenario_id, model_id)
        except Exception as e:
            logger.error(f"更新模型失败: {e}")
            raise
    
    async def delete_model(
        self,
        tenant_id: str,
        scenario_id: str,
        model_id: str
    ) -> bool:
        """删除模型"""
        try:
            result = await self.collection.delete_one({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "model_id": model_id
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"删除模型失败: {e}")
            raise
    
    async def train_model(
        self,
        tenant_id: str,
        scenario_id: str,
        model_id: str,
        request: TrainModelRequest
    ) -> ModelResponse:
        """训练模型（这里是简化版本，实际需要调用训练服务）"""
        try:
            # 更新训练状态为运行中
            update_data = {
                "training_status": TrainingStatus.RUNNING,
                "training_progress": 0.0,
                "status": ModelStatus.TRAINING,
                "updated_at": datetime.utcnow()
            }
            
            await self.collection.update_one(
                {
                    "tenant_id": tenant_id,
                    "scenario_id": scenario_id,
                    "model_id": model_id
                },
                {"$set": update_data}
            )
            
            # TODO: 实际应该调用异步训练任务
            # 这里简化处理，直接模拟训练完成
            logger.info(f"开始训练模型: {model_id}")
            
            return await self.get_model(tenant_id, scenario_id, model_id)
        except Exception as e:
            logger.error(f"训练模型失败: {e}")
            # 更新状态为失败
            await self.collection.update_one(
                {
                    "tenant_id": tenant_id,
                    "scenario_id": scenario_id,
                    "model_id": model_id
                },
                {
                    "$set": {
                        "training_status": TrainingStatus.FAILED,
                        "status": ModelStatus.FAILED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            raise
    
    async def get_training_status(
        self,
        tenant_id: str,
        scenario_id: str,
        model_id: str
    ) -> dict:
        """获取训练状态"""
        try:
            model = await self.get_model(tenant_id, scenario_id, model_id)
            if not model:
                raise ValueError("模型不存在")
            
            return {
                "training_status": model.training_status,
                "training_progress": model.training_progress,
                "training_metrics": model.training_metrics,
                "training_log": model.training_log
            }
        except Exception as e:
            logger.error(f"获取训练状态失败: {e}")
            raise
    
    async def deploy_model(
        self,
        tenant_id: str,
        scenario_id: str,
        model_id: str,
        request: DeployModelRequest
    ) -> ModelResponse:
        """部署模型"""
        try:
            # 更新部署状态
            update_data = {
                "status": ModelStatus.DEPLOYED,
                "deployed_at": datetime.utcnow(),
                "deployment_config": request.deployment_config,
                "updated_at": datetime.utcnow()
            }
            
            await self.collection.update_one(
                {
                    "tenant_id": tenant_id,
                    "scenario_id": scenario_id,
                    "model_id": model_id
                },
                {"$set": update_data}
            )
            
            logger.info(f"模型已部署: {model_id}")
            return await self.get_model(tenant_id, scenario_id, model_id)
        except Exception as e:
            logger.error(f"部署模型失败: {e}")
            raise

