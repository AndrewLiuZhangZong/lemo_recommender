# -*- coding: utf-8 -*-
"""
BFF编排层服务 - gRPC客户端调用
职责：调用召回→精排→重排服务，编排推荐流程
"""
import asyncio
from typing import List, Dict, Optional
import uuid
import time

from app.core.service_discovery import (
    get_recall_channel,
    get_ranking_channel,
    get_reranking_channel
)
from app.grpc_generated.python.recommender.v1 import recommendation_pb2
from app.grpc_generated.python.recommender.v1 import recommendation_pb2_grpc
from google.protobuf import struct_pb2


class BFFRecommendationService:
    """BFF推荐编排服务"""
    
    def __init__(self):
        """初始化gRPC客户端"""
        self.recall_channel = None
        self.ranking_channel = None
        self.reranking_channel = None
        print("[BFFService] 初始化完成")
    
    async def _ensure_channels(self):
        """确保gRPC Channel已创建"""
        if not self.recall_channel:
            self.recall_channel = get_recall_channel()
            self.recall_stub = recommendation_pb2_grpc.RecallServiceStub(self.recall_channel)
        
        if not self.ranking_channel:
            self.ranking_channel = get_ranking_channel()
            self.ranking_stub = recommendation_pb2_grpc.RankingServiceStub(self.ranking_channel)
        
        if not self.reranking_channel:
            self.reranking_channel = get_reranking_channel()
            self.reranking_stub = recommendation_pb2_grpc.RerankingServiceStub(self.reranking_channel)
    
    async def get_recommendations(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        count: int = 20,
        filters: Optional[Dict] = None,
        debug: bool = False
    ) -> Dict:
        """
        获取推荐结果
        
        编排流程：召回 → 精排 → 重排
        """
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # 确保Channel已创建
            await self._ensure_channels()
            
            debug_info = {
                "request_id": request_id,
                "steps": []
            }
            
            # Step 1: 召回
            recall_start = time.time()
            recall_request = recommendation_pb2.MultiRecallRequest(
                tenant_id=tenant_id,
                scenario_id=scenario_id,
                user_id=user_id,
                strategies=[
                    recommendation_pb2.RecallStrategy(
                        name="als_cf",
                        weight=0.4,
                        limit=200
                    ),
                    recommendation_pb2.RecallStrategy(
                        name="hot_items",
                        weight=0.3,
                        limit=100
                    ),
                    recommendation_pb2.RecallStrategy(
                        name="vector",
                        weight=0.3,
                        limit=100
                    )
                ]
            )
            
            if filters:
                recall_request.filters.update(filters)
            
            recall_response = await self.recall_stub.MultiRecall(recall_request)
            recall_time = time.time() - recall_start
            
            if debug:
                debug_info["steps"].append({
                    "name": "recall",
                    "time_ms": int(recall_time * 1000),
                    "count": recall_response.count,
                    "item_ids": list(recall_response.item_ids[:10])  # 只保存前10个用于debug
                })
            
            print(f"[BFFService] 召回完成: {recall_response.count}个候选")
            
            if recall_response.count == 0:
                return {
                    "items": [],
                    "count": 0,
                    "request_id": request_id,
                    "debug_info": debug_info if debug else None
                }
            
            # Step 2: 精排
            ranking_start = time.time()
            ranking_request = recommendation_pb2.RankRequest(
                tenant_id=tenant_id,
                scenario_id=scenario_id,
                user_id=user_id,
                item_ids=list(recall_response.item_ids),
                ranker="deepfm"  # 使用DeepFM排序器
            )
            
            ranking_response = await self.ranking_stub.Rank(ranking_request)
            ranking_time = time.time() - ranking_start
            
            if debug:
                debug_info["steps"].append({
                    "name": "ranking",
                    "time_ms": int(ranking_time * 1000),
                    "count": ranking_response.count,
                    "top_scores": [
                        {"item_id": item.item_id, "score": item.score}
                        for item in ranking_response.ranked_items[:5]
                    ]
                })
            
            print(f"[BFFService] 精排完成: {ranking_response.count}个物品")
            
            # Step 3: 重排
            reranking_start = time.time()
            reranking_request = recommendation_pb2.RerankRequest(
                tenant_id=tenant_id,
                scenario_id=scenario_id,
                user_id=user_id,
                ranked_items=ranking_response.ranked_items,
                rules=[
                    recommendation_pb2.RerankRule(
                        name="diversity"
                    ),
                    recommendation_pb2.RerankRule(
                        name="freshness"
                    )
                ]
            )
            
            reranking_response = await self.reranking_stub.Rerank(reranking_request)
            reranking_time = time.time() - reranking_start
            
            if debug:
                debug_info["steps"].append({
                    "name": "reranking",
                    "time_ms": int(reranking_time * 1000),
                    "count": reranking_response.count
                })
            
            print(f"[BFFService] 重排完成: {reranking_response.count}个物品")
            
            # Step 4: 截取TopN
            final_items = reranking_response.reranked_items[:count]
            
            # 构建返回结果
            result_items = [
                {
                    "item_id": item.item_id,
                    "score": item.score
                }
                for item in final_items
            ]
            
            total_time = time.time() - start_time
            
            if debug:
                debug_info["total_time_ms"] = int(total_time * 1000)
                debug_info["pipeline"] = "recall → ranking → reranking"
            
            return {
                "items": result_items,
                "count": len(result_items),
                "request_id": request_id,
                "debug_info": debug_info if debug else None
            }
            
        except Exception as e:
            print(f"[BFFService] 推荐流程失败: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "items": [],
                "count": 0,
                "request_id": request_id,
                "error": str(e),
                "debug_info": debug_info if debug else None
            }


# 全局单例
_bff_service = None


def get_bff_service() -> BFFRecommendationService:
    """获取BFF服务单例"""
    global _bff_service
    if _bff_service is None:
        _bff_service = BFFRecommendationService()
    return _bff_service
