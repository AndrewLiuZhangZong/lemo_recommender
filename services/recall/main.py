# -*- coding: utf-8 -*-
"""
Recall Service - Multi-strategy recall execution

Responsibilities:
1. Parallel execution of multiple recall strategies
2. Merge and deduplicate recall results
3. Support gRPC interface
4. All configurations loaded from environment variables (K8s ConfigMap)
"""
import asyncio
import sys
import os
import json
from concurrent import futures
from typing import List

import grpc
from motor.motor_asyncio import AsyncIOMotorClient

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.service_config import get_service_config
from app.core.redis_client import get_redis_client
from app.engine.recall.hot_items import HotItemsRecall
from app.engine.recall.collaborative_filtering import CollaborativeFilteringRecall, ItemBasedCFRecall
from app.engine.recall.als_cf import ALSCollaborativeFiltering
from app.grpc_generated.python.recommender.v1 import recommendation_pb2
from app.grpc_generated.python.recommender.v1 import recommendation_pb2_grpc
from app.grpc_generated.python.recommender_common.v1 import health_pb2

# 导入日志
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecallServiceImpl(recommendation_pb2_grpc.RecallServiceServicer):
    """召回服务gRPC实现"""
    
    def __init__(self, db, redis_client, config):
        self.db = db
        self.redis = redis_client
        self.config = config
        
        # 初始化召回策略
        self.recall_strategies = {
            "hot_items": HotItemsRecall(redis_client),
            "user_cf": CollaborativeFilteringRecall(db),
            "item_cf": ItemBasedCFRecall(db),
            "als_cf": ALSCollaborativeFiltering(db, redis_client),
        }
        
        strategies_list = list(self.recall_strategies.keys())
        logger.info("[RecallService] Initialized with strategies: %s", strategies_list)
    
    async def MultiRecall(
        self,
        request: recommendation_pb2.MultiRecallRequest,
        context: grpc.aio.ServicerContext
    ) -> recommendation_pb2.MultiRecallResponse:
        """多路召回"""
        try:
            # 验证必填字段
            if not request.tenant_id or not request.scenario_id or not request.user_id:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("tenant_id, scenario_id, user_id are required")
                return recommendation_pb2.MultiRecallResponse()
            
            # 获取召回策略配置
            strategies = list(request.strategies) if request.strategies else self._get_default_strategies()
            
            # 🚀 并行执行所有召回策略
            tasks = []
            for strategy_config in strategies:
                strategy_name = strategy_config.name
                limit = strategy_config.limit if strategy_config.limit > 0 else 100
                params = dict(strategy_config.params) if strategy_config.params else {}
                
                strategy = self.recall_strategies.get(strategy_name)
                if not strategy:
                    logger.warning(f"[RecallService] 未知的召回策略: {strategy_name}")
                    continue
                
                task = self._execute_single_recall(
                    strategy=strategy,
                    strategy_name=strategy_name,
                    tenant_id=request.tenant_id,
                    scenario_id=request.scenario_id,
                    user_id=request.user_id,
                    limit=limit,
                    params=params
                )
                tasks.append(task)
            
            # 等待所有召回任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 合并结果
            all_candidates = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"[RecallService] 召回任务 {i} 失败: {result}")
                    continue
                if result:
                    all_candidates.extend(result)
            
            # 去重（保持顺序）
            unique_candidates = list(dict.fromkeys(all_candidates))
            
            # 应用过滤条件
            if request.filters and "exclude_items" in request.filters:
                exclude_items = set(request.filters["exclude_items"])
                unique_candidates = [
                    item_id for item_id in unique_candidates
                    if item_id not in exclude_items
                ]
            
            logger.info(f"[RecallService] 召回完成: {len(unique_candidates)}个候选物品")
            
            return recommendation_pb2.MultiRecallResponse(
                item_ids=unique_candidates,
                count=len(unique_candidates)
            )
            
        except Exception as e:
            logger.error(f"[RecallService] MultiRecall failed: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return recommendation_pb2.MultiRecallResponse()
    
    async def HealthCheck(
        self,
        request: health_pb2.HealthCheckRequest,
        context: grpc.aio.ServicerContext
    ) -> health_pb2.HealthCheckResponse:
        """健康检查"""
        return health_pb2.HealthCheckResponse(
            status="healthy",
            service="recall-service",
            version=self.config.service_version
        )
    
    async def _execute_single_recall(
        self,
        strategy,
        strategy_name: str,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        limit: int,
        params: dict
    ) -> List[str]:
        """执行单个召回策略"""
        try:
            item_ids = await strategy.recall(
                tenant_id=tenant_id,
                scenario_id=scenario_id,
                user_id=user_id,
                limit=limit,
                params=params
            )
            logger.info(f"[RecallService] {strategy_name} 召回: {len(item_ids)}个物品")
            return item_ids
        except Exception as e:
            logger.error(f"[RecallService] {strategy_name} 召回失败: {e}")
            return []
    
    def _get_default_strategies(self) -> List[recommendation_pb2.RecallStrategy]:
        """获取默认召回策略"""
        try:
            strategies_json = json.loads(self.config.recall_strategies)
            return [
                recommendation_pb2.RecallStrategy(
                    name=s["name"],
                    weight=s.get("weight", 1.0),
                    limit=s.get("limit", 100)
                )
                for s in strategies_json
            ]
        except Exception as e:
            logger.error(f"[RecallService] 解析默认召回策略失败: {e}")
            return [
                recommendation_pb2.RecallStrategy(name="hot_items", weight=1.0, limit=100)
            ]


async def serve():
    """启动gRPC服务"""
    # 加载配置
    config = get_service_config()
    config.service_name = "recall-service"
    config.port = int(os.getenv("PORT", "8081"))
    
    # 连接数据库
    mongo_client = AsyncIOMotorClient(config.mongodb_url)
    db = mongo_client[config.mongodb_database]
    
    # 连接Redis
    redis_client = await get_redis_client()
    
    # 创建gRPC服务
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )
    
    # 注册服务
    recommendation_pb2_grpc.add_RecallServiceServicer_to_server(
        RecallServiceImpl(db, redis_client, config),
        server
    )
    
    # 监听端口
    server.add_insecure_port(f"{config.host}:{config.port}")
    
    logger.info(f"[RecallService] 启动gRPC服务于 {config.host}:{config.port}")
    
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
