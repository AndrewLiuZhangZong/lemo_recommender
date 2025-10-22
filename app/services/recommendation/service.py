"""
推荐服务
"""
from typing import List, Dict, Any, Optional
import time
import uuid
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.recommendation import (
    RecommendRequest,
    RecommendResponse,
    RecommendedItem,
    DebugInfo
)
from app.services.scenario.service import ScenarioService
from app.services.item.service import ItemService
from app.engine.recall.hot_items import HotItemsRecall
from app.engine.recall.collaborative_filtering import CollaborativeFilteringRecall, ItemBasedCFRecall
from app.engine.ranker.simple_ranker import SimpleScoreRanker, RandomRanker
from app.engine.reranker.diversity import DiversityReranker, FreshnessReranker


class RecommendationService:
    """推荐服务"""
    
    def __init__(self, db: AsyncIOMotorDatabase, redis_client=None):
        self.db = db
        self.redis = redis_client
        
        # 服务依赖
        self.scenario_service = ScenarioService(db)
        self.item_service = ItemService(db)
        
        # 召回策略注册表
        self.recall_strategies = {
            "hot_items": HotItemsRecall(redis_client),
            "user_cf": CollaborativeFilteringRecall(db),
            "item_cf": ItemBasedCFRecall(db),
        }
        
        # 排序器注册表
        self.rankers = {
            "simple_score": SimpleScoreRanker(db),
            "random": RandomRanker(),
        }
        
        # 重排器注册表
        self.rerankers = {
            "diversity": DiversityReranker(db),
            "freshness": FreshnessReranker(db),
        }
    
    async def recommend(
        self,
        tenant_id: str,
        user_id: str,
        request: RecommendRequest
    ) -> RecommendResponse:
        """推荐主流程"""
        
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # 1. 加载场景配置
            scenario = await self.scenario_service.get_scenario(
                tenant_id=tenant_id,
                scenario_id=request.scenario_id
            )
            
            if not scenario:
                raise ValueError(f"场景不存在: {request.scenario_id}")
            
            config = scenario.config
            
            # 2. 召回阶段
            recall_start = time.time()
            candidate_item_ids = await self._multi_recall(
                tenant_id=tenant_id,
                scenario_id=request.scenario_id,
                user_id=user_id,
                config=config,
                filters=request.filters
            )
            recall_time = (time.time() - recall_start) * 1000
            
            if not candidate_item_ids:
                # 无召回结果，返回空列表
                return self._empty_response(
                    request_id, tenant_id, user_id, request.scenario_id,
                    recall_time, request.debug
                )
            
            # 3. 排序阶段
            rank_start = time.time()
            ranked_items = await self._rank(
                tenant_id=tenant_id,
                scenario_id=request.scenario_id,
                user_id=user_id,
                item_ids=candidate_item_ids,
                config=config
            )
            rank_time = (time.time() - rank_start) * 1000
            
            # 4. 重排阶段
            rerank_start = time.time()
            reranked_items = await self._rerank(
                tenant_id=tenant_id,
                scenario_id=request.scenario_id,
                user_id=user_id,
                ranked_items=ranked_items,
                config=config
            )
            rerank_time = (time.time() - rerank_start) * 1000
            
            # 5. 截取Top N
            top_items = reranked_items[:request.count]
            
            # 6. 填充物品详情
            result_items = await self._fill_item_details(
                tenant_id=tenant_id,
                scenario_id=request.scenario_id,
                scored_items=top_items
            )
            
            # 7. 构建响应
            total_time = (time.time() - start_time) * 1000
            
            debug_info = None
            if request.debug:
                debug_info = DebugInfo(
                    recall_count=len(candidate_item_ids),
                    recall_time_ms=recall_time,
                    rank_time_ms=rank_time,
                    rerank_time_ms=rerank_time,
                    total_time_ms=total_time
                )
            
            return RecommendResponse(
                request_id=request_id,
                tenant_id=tenant_id,
                user_id=user_id,
                scenario_id=request.scenario_id,
                items=result_items,
                debug_info=debug_info
            )
            
        except Exception as e:
            print(f"推荐失败: {e}")
            raise
    
    async def _multi_recall(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        config: Any,
        filters: Dict[str, Any]
    ) -> List[str]:
        """多路召回"""
        
        recall_config = config.recall
        strategies = recall_config.get("strategies", [])
        
        if not strategies:
            # 默认召回策略
            strategies = [
                {"name": "user_cf", "weight": 0.5, "limit": 100},
                {"name": "item_cf", "weight": 0.5, "limit": 100}
            ]
        
        all_candidates = []
        
        for strategy_config in strategies:
            strategy_name = strategy_config.get("name")
            limit = strategy_config.get("limit", 100)
            params = strategy_config.get("params", {})
            
            # 获取召回策略
            strategy = self.recall_strategies.get(strategy_name)
            if not strategy:
                print(f"未知的召回策略: {strategy_name}")
                continue
            
            # 执行召回
            try:
                item_ids = await strategy.recall(
                    tenant_id=tenant_id,
                    scenario_id=scenario_id,
                    user_id=user_id,
                    limit=limit,
                    params=params
                )
                all_candidates.extend(item_ids)
            except Exception as e:
                print(f"召回策略 {strategy_name} 失败: {e}")
        
        # 去重
        unique_candidates = list(dict.fromkeys(all_candidates))
        
        # 应用过滤条件
        if filters and filters.get("exclude_items"):
            exclude_items = set(filters["exclude_items"])
            unique_candidates = [
                item_id for item_id in unique_candidates
                if item_id not in exclude_items
            ]
        
        return unique_candidates
    
    async def _rank(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        item_ids: List[str],
        config: Any
    ) -> List[tuple[str, float]]:
        """排序"""
        
        rank_config = config.rank
        ranker_name = rank_config.model if hasattr(rank_config, 'model') else "simple_score"
        
        # 获取排序器
        ranker = self.rankers.get(ranker_name)
        if not ranker:
            print(f"未知的排序器: {ranker_name}，使用默认排序器")
            ranker = self.rankers["simple_score"]
        
        # 执行排序
        ranked_items = await ranker.rank(
            tenant_id=tenant_id,
            scenario_id=scenario_id,
            user_id=user_id,
            item_ids=item_ids
        )
        
        return ranked_items
    
    async def _rerank(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        ranked_items: List[tuple[str, float]],
        config: Any
    ) -> List[tuple[str, float]]:
        """重排"""
        
        rerank_config = config.rerank
        rules = rerank_config.get("rules", [])
        
        if not rules:
            return ranked_items
        
        result = ranked_items
        
        for rule_config in rules:
            rule_name = rule_config.get("name")
            
            # 获取重排器
            reranker = self.rerankers.get(rule_name)
            if not reranker:
                print(f"未知的重排规则: {rule_name}")
                continue
            
            # 执行重排
            try:
                result = await reranker.rerank(
                    tenant_id=tenant_id,
                    scenario_id=scenario_id,
                    user_id=user_id,
                    ranked_items=result
                )
            except Exception as e:
                print(f"重排规则 {rule_name} 失败: {e}")
        
        return result
    
    async def _fill_item_details(
        self,
        tenant_id: str,
        scenario_id: str,
        scored_items: List[tuple[str, float]]
    ) -> List[RecommendedItem]:
        """填充物品详情"""
        
        item_ids = [item_id for item_id, _ in scored_items]
        
        # 批量获取物品信息
        items = await self.item_service.get_items_by_ids(
            tenant_id=tenant_id,
            scenario_id=scenario_id,
            item_ids=item_ids
        )
        
        # 构建item_id -> item映射
        item_map = {item.item_id: item for item in items}
        
        # 构建结果列表
        result = []
        for item_id, score in scored_items:
            item = item_map.get(item_id)
            if item:
                result.append(RecommendedItem(
                    item_id=item_id,
                    score=round(score, 4),
                    metadata=item.metadata
                ))
        
        return result
    
    def _empty_response(
        self,
        request_id: str,
        tenant_id: str,
        user_id: str,
        scenario_id: str,
        recall_time: float,
        debug: bool
    ) -> RecommendResponse:
        """空结果响应"""
        
        debug_info = None
        if debug:
            debug_info = DebugInfo(
                recall_count=0,
                recall_time_ms=recall_time,
                rank_time_ms=0,
                rerank_time_ms=0,
                total_time_ms=recall_time
            )
        
        return RecommendResponse(
            request_id=request_id,
            tenant_id=tenant_id,
            user_id=user_id,
            scenario_id=scenario_id,
            items=[],
            debug_info=debug_info
        )

