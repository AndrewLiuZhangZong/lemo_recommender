"""
数据分析服务
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """数据分析服务"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        # 真实场景下应该从事件日志表或数据仓库获取数据
        # 目前从现有collection中模拟统计
        self.scenarios_collection = db.scenarios
        self.items_collection = db.items
        self.models_collection = db.models
        self.experiments_collection = db.experiments
    
    async def get_dashboard_data(
        self,
        tenant_id: str,
        scenario_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取仪表板核心数据
        
        注意：当前为基于现有数据的模拟实现
        生产环境应从事件追踪系统（如ClickHouse、ES）获取真实数据
        """
        try:
            # 查询条件
            query = {}
            if tenant_id:
                query["tenant_id"] = tenant_id
            if scenario_id:
                query["scenario_id"] = scenario_id
            
            # 统计物品数量（作为推荐池大小的代理指标）
            total_items = await self.items_collection.count_documents(query)
            
            # 统计活跃场景数
            scenario_query = {"tenant_id": tenant_id} if tenant_id else {}
            active_scenarios = await self.scenarios_collection.count_documents(
                {**scenario_query, "status": "active"}
            )
            
            # 统计运行中的实验数
            experiment_query = {"tenant_id": tenant_id} if tenant_id else {}
            running_experiments = await self.experiments_collection.count_documents(
                {**experiment_query, "status": "running"}
            )
            
            # 注意：推荐相关指标需要接入事件追踪系统才能获取真实数据
            # 当前只返回配置数据的真实统计（物品数、场景数、实验数）
            dashboard_data = {
                "overview": {
                    "total_recommendations": 0,  # 需要事件日志系统
                    "ctr": 0.0,  # 需要事件日志系统
                    "conversion_rate": 0.0,  # 需要事件日志系统
                    "active_users": 0,  # 需要事件日志系统
                    "total_items": total_items,  # ✅ 真实数据：从items collection统计
                    "active_scenarios": active_scenarios,  # ✅ 真实数据：从scenarios collection统计
                    "running_experiments": running_experiments,  # ✅ 真实数据：从experiments collection统计
                },
                "trend": {
                    "recommendations_growth": 0.0,
                    "ctr_growth": 0.0,
                    "conversion_growth": 0.0,
                    "users_growth": 0.0,
                },
                "data_source": "partial",  # 部分数据
                "message": "推荐指标需要接入事件追踪系统（如Kafka+ClickHouse），当前仅显示配置数据统计"
            }
            
            logger.info(f"获取仪表板数据成功 - tenant: {tenant_id}, items: {total_items}")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"获取仪表板数据失败: {e}")
            raise
    
    async def get_metrics_trend(
        self,
        tenant_id: str,
        metrics: List[str],
        scenario_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        granularity: str = "hour"
    ) -> Dict[str, Any]:
        """
        获取指标趋势数据
        
        生产环境应从时序数据库获取（如ClickHouse、TimescaleDB）
        """
        try:
            # 时间点（最近24小时，每4小时一个点）
            time_points = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
            
            # 返回空数据，等待接入真实事件追踪系统
            trend_data = {
                "time_points": time_points,
                "metrics": {
                    "impressions": {
                        "label": "推荐曝光",
                        "data": [0, 0, 0, 0, 0, 0, 0],  # 空数据
                        "unit": "次"
                    },
                    "clicks": {
                        "label": "推荐点击",
                        "data": [0, 0, 0, 0, 0, 0, 0],  # 空数据
                        "unit": "次"
                    },
                    "ctr": {
                        "label": "点击率",
                        "data": [0, 0, 0, 0, 0, 0, 0],  # 空数据
                        "unit": "%"
                    },
                    "conversions": {
                        "label": "转化数",
                        "data": [0, 0, 0, 0, 0, 0, 0],  # 空数据
                        "unit": "次"
                    }
                },
                "granularity": granularity,
                "data_source": "empty",  # 标记为空数据
                "message": "需要接入事件追踪系统获取真实推荐数据"
            }
            
            # 只返回请求的指标
            if metrics:
                trend_data["metrics"] = {
                    k: v for k, v in trend_data["metrics"].items()
                    if k in metrics
                }
            
            return trend_data
            
        except Exception as e:
            logger.error(f"获取指标趋势失败: {e}")
            raise
    
    async def get_item_distribution(
        self,
        tenant_id: str,
        dimension: str = "scenario",
        scenario_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取物品分布统计
        
        支持维度：scenario（场景）、category（类目）、status（状态）
        """
        try:
            query = {}
            if tenant_id:
                query["tenant_id"] = tenant_id
            if scenario_id:
                query["scenario_id"] = scenario_id
            
            # 按维度聚合
            if dimension == "scenario":
                # 按场景统计物品分布
                pipeline = [
                    {"$match": query},
                    {"$group": {
                        "_id": "$scenario_id",
                        "count": {"$sum": 1}
                    }},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ]
                
                cursor = self.items_collection.aggregate(pipeline)
                results = await cursor.to_list(length=10)
                
                distribution = {
                    "dimension": "场景分布",
                    "items": [
                        {
                            "name": result["_id"] or "未分类",
                            "value": result["count"]
                        }
                        for result in results
                    ]
                }
                
            elif dimension == "status":
                # 按状态统计
                pipeline = [
                    {"$match": query},
                    {"$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }}
                ]
                
                cursor = self.items_collection.aggregate(pipeline)
                results = await cursor.to_list(length=10)
                
                status_labels = {
                    "active": "启用",
                    "inactive": "禁用",
                    "archived": "归档"
                }
                
                distribution = {
                    "dimension": "状态分布",
                    "items": [
                        {
                            "name": status_labels.get(result["_id"], result["_id"]),
                            "value": result["count"]
                        }
                        for result in results
                    ]
                }
            else:
                # 默认返回模拟的类目分布
                distribution = {
                    "dimension": "类目分布",
                    "items": [
                        {"name": "电子产品", "value": 3580},
                        {"name": "服装鞋包", "value": 2360},
                        {"name": "食品饮料", "value": 1850},
                        {"name": "图书音像", "value": 1450},
                        {"name": "其他", "value": 890},
                    ],
                    "data_source": "simulated"
                }
            
            return distribution
            
        except Exception as e:
            logger.error(f"获取物品分布失败: {e}")
            raise
    
    async def get_user_behavior_analysis(
        self,
        tenant_id: str,
        scenario_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取用户行为分析
        
        生产环境应从用户行为日志分析（如通过Flink实时计算）
        """
        try:
            # 返回空数据，等待接入用户行为追踪系统
            behavior_data = {
                "user_metrics": {
                    "total_users": 0,
                    "active_users": 0,
                    "new_users": 0,
                    "returning_users": 0,
                },
                "engagement": {
                    "avg_session_duration": 0,
                    "avg_page_views": 0.0,
                    "bounce_rate": 0.0,
                    "avg_recommendations_per_session": 0.0,
                },
                "conversion_funnel": [
                    {"stage": "曝光", "users": 0, "rate": 0.0},
                    {"stage": "点击", "users": 0, "rate": 0.0},
                    {"stage": "查看详情", "users": 0, "rate": 0.0},
                    {"stage": "加购", "users": 0, "rate": 0.0},
                    {"stage": "下单", "users": 0, "rate": 0.0},
                ],
                "top_behaviors": [
                    {"action": "浏览推荐", "count": 0, "percentage": 0.0},
                    {"action": "点击推荐", "count": 0, "percentage": 0.0},
                    {"action": "搜索", "count": 0, "percentage": 0.0},
                    {"action": "收藏", "count": 0, "percentage": 0.0},
                    {"action": "分享", "count": 0, "percentage": 0.0},
                ],
                "data_source": "empty",
                "message": "需要接入用户行为追踪系统获取真实数据"
            }
            
            return behavior_data
            
        except Exception as e:
            logger.error(f"获取用户行为分析失败: {e}")
            raise

