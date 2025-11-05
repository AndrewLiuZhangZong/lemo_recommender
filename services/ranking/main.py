# -*- coding: utf-8 -*-
"""
精排服务 - gRPC实现
职责：对召回的候选物品进行精排（DeepFM/SimpleScore/Random）
"""
import sys
import os
import asyncio
from typing import List, Tuple
from concurrent import futures

import grpc
from motor.motor_asyncio import AsyncIOMotorClient

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.config import settings
from app.core.service_config import ServiceConfig
from app.engine.ranker.simple_ranker import SimpleScoreRanker, RandomRanker
from app.engine.ranker.deep_ranker import DeepRanker
from app.grpc_generated.python.recommender.v1 import recommendation_pb2
from app.grpc_generated.python.recommender.v1 import recommendation_pb2_grpc
from app.grpc_generated.python.recommender_common.v1 import health_pb2


class RankingService:
    """精排服务核心逻辑"""
    
    def __init__(self, db):
        self.db = db
        
        # 初始化排序器
        self.rankers = {
            "simple_score": SimpleScoreRanker(db),
            "random": RandomRanker(),
            "deepfm": DeepRanker(db),
        }
        
        print(f"[RankingService] 初始化完成，支持排序器: {list(self.rankers.keys())}")
    
    async def rank(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        item_ids: List[str],
        ranker_name: str = "simple_score"
    ) -> List[Tuple[str, float]]:
        """
        对物品进行排序
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            user_id: 用户ID
            item_ids: 待排序的物品ID列表
            ranker_name: 排序器名称
            
        Returns:
            排序后的 (item_id, score) 列表
        """
        if not item_ids:
            return []
        
        # 获取排序器
        ranker = self.rankers.get(ranker_name)
        if not ranker:
            print(f"[RankingService] 未知的排序器: {ranker_name}，使用默认排序器")
            ranker = self.rankers["simple_score"]
        
        # 执行排序
        try:
            ranked_items = await ranker.rank(
                tenant_id=tenant_id,
                scenario_id=scenario_id,
                user_id=user_id,
                item_ids=item_ids
            )
            
            print(f"[RankingService] 排序完成: {len(ranked_items)}个物品")
            return ranked_items
        except Exception as e:
            print(f"[RankingService] 排序失败: {e}")
            # 降级：返回原始顺序
            return [(item_id, 0.0) for item_id in item_ids]


class RankingServicer(recommendation_pb2_grpc.RankingServiceServicer):
    """精排服务gRPC实现"""
    
    def __init__(self, ranking_service: RankingService):
        self.ranking_service = ranking_service
    
    async def Rank(self, request, context):
        """精排接口"""
        try:
            # 执行排序
            ranked_items = await self.ranking_service.rank(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                user_id=request.user_id,
                item_ids=list(request.item_ids),
                ranker_name=request.ranker or "simple_score"
            )
            
            # 构建响应
            scored_items = [
                recommendation_pb2.ScoredItem(item_id=item_id, score=score)
                for item_id, score in ranked_items
            ]
            
            return recommendation_pb2.RankResponse(
                ranked_items=scored_items,
                count=len(scored_items)
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Ranking failed: {str(e)}")
            return recommendation_pb2.RankResponse()
    
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
    port = int(os.getenv("GRPC_PORT", "8082"))
    
    # 连接数据库
    mongo_url = config.get_mongodb_url()
    mongo_client = AsyncIOMotorClient(mongo_url)
    db = mongo_client[config.mongodb_database]
    
    # 初始化精排服务
    ranking_service = RankingService(db)
    
    # 创建gRPC服务器
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )
    
    # 注册服务
    recommendation_pb2_grpc.add_RankingServiceServicer_to_server(
        RankingServicer(ranking_service),
        server
    )
    
    # 启动服务器
    server.add_insecure_port(f"{host}:{port}")
    await server.start()
    
    print(f"[RankingService] gRPC服务启动于 {host}:{port}")
    print(f"[RankingService] MongoDB: {config.mongodb_host}")
    print(f"[RankingService] 支持排序器: {list(ranking_service.rankers.keys())}")
    
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
