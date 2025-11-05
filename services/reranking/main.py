# -*- coding: utf-8 -*-
"""
重排服务 - gRPC实现
职责：应用多样性、新鲜度、业务规则进行重排
"""
import sys
import os
import asyncio
from typing import List, Tuple, Dict
from concurrent import futures

import grpc
from motor.motor_asyncio import AsyncIOMotorClient
from google.protobuf import struct_pb2

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.config import settings
from app.core.service_config import ServiceConfig
from app.engine.reranker.diversity import DiversityReranker, FreshnessReranker
from app.grpc_generated.python.recommender.v1 import recommendation_pb2
from app.grpc_generated.python.recommender.v1 import recommendation_pb2_grpc
from app.grpc_generated.python.recommender_common.v1 import health_pb2


class RerankingService:
    """重排服务核心逻辑"""
    
    def __init__(self, db):
        self.db = db
        
        # 初始化重排器
        self.rerankers = {
            "diversity": DiversityReranker(db),
            "freshness": FreshnessReranker(db),
        }
        
        print(f"[RerankingService] 初始化完成，支持重排器: {list(self.rerankers.keys())}")
    
    async def rerank(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        ranked_items: List[Tuple[str, float]],
        rules: List[Dict] = None
    ) -> List[Tuple[str, float]]:
        """
        对已排序的物品进行重排
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            user_id: 用户ID
            ranked_items: 已排序的 (item_id, score) 列表
            rules: 重排规则配置列表
            
        Returns:
            重排后的 (item_id, score) 列表
        """
        if not ranked_items:
            return []
        
        if not rules:
            # 默认重排规则
            rules = [
                {"name": "diversity"},
                {"name": "freshness"}
            ]
        
        result = ranked_items
        
        for rule_config in rules:
            rule_name = rule_config.get("name")
            
            # 获取重排器
            reranker = self.rerankers.get(rule_name)
            if not reranker:
                print(f"[RerankingService] 未知的重排规则: {rule_name}")
                continue
            
            # 执行重排
            try:
                result = await reranker.rerank(
                    tenant_id=tenant_id,
                    scenario_id=scenario_id,
                    user_id=user_id,
                    ranked_items=result
                )
                print(f"[RerankingService] 应用重排规则: {rule_name}")
            except Exception as e:
                print(f"[RerankingService] 重排规则 {rule_name} 失败: {e}")
        
        print(f"[RerankingService] 重排完成: {len(result)}个物品")
        return result


class RerankingServicer(recommendation_pb2_grpc.RerankingServiceServicer):
    """重排服务gRPC实现"""
    
    def __init__(self, reranking_service: RerankingService):
        self.reranking_service = reranking_service
    
    async def Rerank(self, request, context):
        """重排接口"""
        try:
            # 转换输入
            ranked_items = [
                (item.item_id, item.score)
                for item in request.ranked_items
            ]
            
            # 解析重排规则
            rules = []
            for rule in request.rules:
                rule_dict = {"name": rule.name}
                if rule.params:
                    rule_dict["params"] = dict(rule.params)
                rules.append(rule_dict)
            
            # 执行重排
            reranked_items = await self.reranking_service.rerank(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                user_id=request.user_id,
                ranked_items=ranked_items,
                rules=rules if rules else None
            )
            
            # 构建响应
            scored_items = [
                recommendation_pb2.ScoredItem(item_id=item_id, score=score)
                for item_id, score in reranked_items
            ]
            
            return recommendation_pb2.RerankResponse(
                reranked_items=scored_items,
                count=len(scored_items)
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Reranking failed: {str(e)}")
            return recommendation_pb2.RerankResponse()
    
    async def HealthCheck(self, request, context):
        """健康检查"""
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.SERVING
        )


async def serve():
    """启动gRPC服务"""
    # 从ConfigMap获取配置
    config = ServiceConfig()
    host = os.getenv("GRPC_HOST", "0.0.0.0")
    port = int(os.getenv("GRPC_PORT", "8083"))
    
    # 连接数据库
    mongo_url = config.get_mongodb_url()
    mongo_client = AsyncIOMotorClient(mongo_url)
    db = mongo_client[config.mongodb_database]
    
    # 初始化重排服务
    reranking_service = RerankingService(db)
    
    # 创建gRPC服务器
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )
    
    # 注册服务
    recommendation_pb2_grpc.add_RerankingServiceServicer_to_server(
        RerankingServicer(reranking_service),
        server
    )
    
    # 启动服务器
    server.add_insecure_port(f"{host}:{port}")
    await server.start()
    
    print(f"[RerankingService] gRPC服务启动于 {host}:{port}")
    print(f"[RerankingService] MongoDB: {config.mongodb_host}")
    print(f"[RerankingService] 支持重排器: {list(reranking_service.rerankers.keys())}")
    
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
