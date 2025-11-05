# -*- coding: utf-8 -*-
"""
特征工程服务 - gRPC实现
职责：特征提取、特征组合、特征转换、特征存储
"""
import sys
import os
import asyncio
from datetime import datetime
from typing import List, Dict
from concurrent import futures

import grpc
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.config import settings
from app.core.service_config import ServiceConfig
from app.grpc_generated.python.recommender_common.v1 import health_pb2


class FeatureEngineeringService:
    """特征工程服务核心逻辑"""
    
    def __init__(self, db):
        self.db = db
        self.features = db.features
        print("[FeatureEngineeringService] 初始化完成")
    
    async def extract_features(
        self,
        tenant_id: str,
        scenario_id: str,
        entity_type: str,  # user or item
        entity_id: str
    ) -> Dict:
        """提取特征"""
        try:
            # 这里应该实现实际的特征提取逻辑
            # 简化实现：从数据库读取
            features = {}
            
            if entity_type == "user":
                user_profile = await self.db.user_profiles.find_one({
                    "tenant_id": tenant_id,
                    "scenario_id": scenario_id,
                    "user_id": entity_id
                })
                if user_profile:
                    features = {
                        "view_count": user_profile.get("view_count", 0),
                        "like_count": user_profile.get("like_count", 0),
                        "preferred_tags": user_profile.get("preferred_tags", [])
                    }
            elif entity_type == "item":
                item = await self.db.items.find_one({
                    "tenant_id": tenant_id,
                    "scenario_id": scenario_id,
                    "item_id": entity_id
                })
                if item and "metadata" in item:
                    features = item["metadata"]
            
            print(f"[FeatureEngineeringService] 提取特征: {entity_type}/{entity_id}")
            return features
        except Exception as e:
            print(f"[FeatureEngineeringService] 提取特征失败: {e}")
            return {}
    
    async def compute_batch_features(
        self,
        tenant_id: str,
        scenario_id: str,
        entity_ids: List[str]
    ) -> List[Dict]:
        """批量计算特征"""
        try:
            results = []
            for entity_id in entity_ids:
                features = await self.extract_features(
                    tenant_id, scenario_id, "item", entity_id
                )
                results.append(features)
            
            print(f"[FeatureEngineeringService] 批量计算特征: {len(results)}个")
            return results
        except Exception as e:
            print(f"[FeatureEngineeringService] 批量计算特征失败: {e}")
            return []


async def serve():
    """启动gRPC服务"""
    config = ServiceConfig()
    host = os.getenv("GRPC_HOST", "0.0.0.0")
    port = int(os.getenv("GRPC_PORT", "8092"))
    
    mongo_url = config.get_mongodb_url()
    mongo_client = AsyncIOMotorClient(mongo_url)
    db = mongo_client[config.mongodb_database]
    
    feature_service = FeatureEngineeringService(db)
    
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )
    
    # 注意：这里需要实际的proto定义，暂时简化
    server.add_insecure_port(f"{host}:{port}")
    await server.start()
    
    print(f"[FeatureEngineeringService] gRPC服务启动于 {host}:{port}")
    print(f"[FeatureEngineeringService] MongoDB: {config.mongodb_host}")
    
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
