# -*- coding: utf-8 -*-
"""
模型训练服务 - gRPC实现
职责：深度学习模型训练（DeepFM、双塔、Wide&Deep）、模型版本管理、GPU调度
"""
import sys
import os
import asyncio
from datetime import datetime
from typing import Optional
from concurrent import futures

import grpc
from motor.motor_asyncio import AsyncIOMotorClient

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.config import settings
from app.core.service_config import ServiceConfig
from app.grpc_generated.python.recommender.v1 import model_pb2
from app.grpc_generated.python.recommender.v1 import model_pb2_grpc


class ModelTrainingService:
    """模型训练服务核心逻辑"""
    
    def __init__(self, db):
        self.db = db
        self.models = db.models
        self.training_jobs = {}
        print("[ModelTrainingService] 初始化完成")
    
    async def start_training(
        self,
        tenant_id: str,
        scenario_id: str,
        model_name: str,
        model_config: dict
    ) -> Optional[dict]:
        """启动模型训练任务"""
        try:
            job_id = f"train_{model_name}_{int(datetime.utcnow().timestamp())}"
            
            job_doc = {
                "job_id": job_id,
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "model_name": model_name,
                "model_config": model_config,
                "status": "pending",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.models.insert_one(job_doc)
            job_doc["_id"] = result.inserted_id
            
            # 存储到内存（实际应该用Celery或其他任务队列）
            self.training_jobs[job_id] = job_doc
            
            print(f"[ModelTrainingService] 启动训练任务: {job_id}")
            return job_doc
        except Exception as e:
            print(f"[ModelTrainingService] 启动训练失败: {e}")
            return None
    
    async def get_training_status(self, job_id: str) -> Optional[dict]:
        """获取训练任务状态"""
        try:
            # 先从内存查询
            if job_id in self.training_jobs:
                return self.training_jobs[job_id]
            
            # 从数据库查询
            job = await self.models.find_one({"job_id": job_id})
            return job
        except Exception as e:
            print(f"[ModelTrainingService] 获取训练状态失败: {e}")
            return None
    
    async def list_models(self, tenant_id: str, scenario_id: str) -> list:
        """列出所有模型"""
        try:
            cursor = self.models.find({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "status": "completed"
            }).sort("created_at", -1)
            
            models = await cursor.to_list(length=100)
            return models
        except Exception as e:
            print(f"[ModelTrainingService] 列出模型失败: {e}")
            return []


class ModelTrainingServicer(model_pb2_grpc.ModelServiceServicer):
    """模型训练服务gRPC实现"""
    
    def __init__(self, training_service: ModelTrainingService):
        self.training_service = training_service
    
    async def StartTraining(self, request, context):
        """启动模型训练"""
        try:
            model_config = dict(request.config) if request.config else {}
            
            job = await self.training_service.start_training(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                model_name=request.model_name,
                model_config=model_config
            )
            
            if job:
                return model_pb2.StartTrainingResponse(
                    job_id=job["job_id"],
                    status="pending"
                )
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Failed to start training")
                return model_pb2.StartTrainingResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Start training failed: {str(e)}")
            return model_pb2.StartTrainingResponse()
    
    async def GetTrainingStatus(self, request, context):
        """获取训练状态"""
        try:
            job = await self.training_service.get_training_status(request.job_id)
            
            if job:
                return model_pb2.GetTrainingStatusResponse(
                    job_id=job["job_id"],
                    status=job.get("status", "unknown"),
                    progress=job.get("progress", 0.0),
                    message=job.get("message", "")
                )
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Training job not found")
                return model_pb2.GetTrainingStatusResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Get training status failed: {str(e)}")
            return model_pb2.GetTrainingStatusResponse()


async def serve():
    """启动gRPC服务"""
    config = ServiceConfig()
    host = os.getenv("GRPC_HOST", "0.0.0.0")
    port = int(os.getenv("GRPC_PORT", "8091"))
    
    mongo_url = config.get_mongodb_url()
    mongo_client = AsyncIOMotorClient(mongo_url)
    db = mongo_client[config.mongodb_database]
    
    training_service = ModelTrainingService(db)
    
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=5),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )
    
    model_pb2_grpc.add_ModelServiceServicer_to_server(
        ModelTrainingServicer(training_service),
        server
    )
    
    server.add_insecure_port(f"{host}:{port}")
    await server.start()
    
    print(f"[ModelTrainingService] gRPC服务启动于 {host}:{port}")
    print(f"[ModelTrainingService] MongoDB: {config.mongodb_host}")
    
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
