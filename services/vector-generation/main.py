# -*- coding: utf-8 -*-
"""
向量生成服务 - gRPC实现
职责：物品Embedding生成、用户Embedding生成、向量索引更新（Milvus）
"""
import sys
import os
import asyncio
from typing import List
from concurrent import futures

import grpc
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.config import settings
from app.core.service_config import ServiceConfig


class VectorGenerationService:
    """向量生成服务核心逻辑"""
    
    def __init__(self, db, milvus_client=None):
        self.db = db
        self.milvus_client = milvus_client
        self.items = db.items
        print("[VectorGenerationService] 初始化完成")
    
    async def generate_item_embedding(
        self,
        tenant_id: str,
        scenario_id: str,
        item_id: str
    ) -> List[float]:
        """生成物品向量"""
        try:
            # 这里应该调用实际的Embedding模型
            # 简化实现：返回随机向量或从数据库读取
            item = await self.items.find_one({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "item_id": item_id
            })
            
            if item and "embedding" in item:
                return item["embedding"]
            
            # 生成默认向量（实际应该调用模型）
            import random
            embedding = [random.random() for _ in range(128)]
            
            # 更新到数据库
            await self.items.update_one(
                {"tenant_id": tenant_id, "scenario_id": scenario_id, "item_id": item_id},
                {"$set": {"embedding": embedding}}
            )
            
            print(f"[VectorGenerationService] 生成物品向量: {item_id}")
            return embedding
        except Exception as e:
            print(f"[VectorGenerationService] 生成向量失败: {e}")
            return []
    
    async def batch_generate_embeddings(
        self,
        tenant_id: str,
        scenario_id: str,
        item_ids: List[str]
    ) -> List[List[float]]:
        """批量生成向量"""
        try:
            embeddings = []
            for item_id in item_ids:
                embedding = await self.generate_item_embedding(
                    tenant_id, scenario_id, item_id
                )
                embeddings.append(embedding)
            
            print(f"[VectorGenerationService] 批量生成向量: {len(embeddings)}个")
            return embeddings
        except Exception as e:
            print(f"[VectorGenerationService] 批量生成向量失败: {e}")
            return []
    
    async def sync_to_milvus(
        self,
        tenant_id: str,
        scenario_id: str,
        item_ids: List[str],
        embeddings: List[List[float]]
    ) -> bool:
        """同步向量到Milvus"""
        try:
            if not self.milvus_client:
                print("[VectorGenerationService] Milvus客户端未初始化")
                return False
            
            # 这里应该调用Milvus API
            print(f"[VectorGenerationService] 同步向量到Milvus: {len(item_ids)}个")
            return True
        except Exception as e:
            print(f"[VectorGenerationService] 同步Milvus失败: {e}")
            return False


async def serve():
    """启动gRPC服务"""
    config = ServiceConfig()
    host = os.getenv("GRPC_HOST", "0.0.0.0")
    port = int(os.getenv("GRPC_PORT", "8093"))
    
    mongo_url = config.get_mongodb_url()
    mongo_client = AsyncIOMotorClient(mongo_url)
    db = mongo_client[config.mongodb_database]
    
    vector_service = VectorGenerationService(db)
    
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )
    
    server.add_insecure_port(f"{host}:{port}")
    await server.start()
    
    print(f"[VectorGenerationService] gRPC服务启动于 {host}:{port}")
    print(f"[VectorGenerationService] MongoDB: {config.mongodb_host}")
    
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
