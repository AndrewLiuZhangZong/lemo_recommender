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
            
            # 生产环境应从事件日志统计，这里返回模拟数据
            dashboard_data = {
                "overview": {
                    "total_recommendations": 1285430,  # 总推荐次数（应从事件日志统计）
                    "ctr": 18.6,  # 点击率（应从事件日志统计）
                    "conversion_rate": 5.8,  # 转化率（应从事件日志统计）
                    "active_users": 52380,  # 活跃用户（应从事件日志统计）
                    "total_items": total_items,  # 物品池大小
                    "active_scenarios": active_scenarios,  # 活跃场景数
                    "running_experiments": running_experiments,  # 运行中的实验数
                },
                "trend": {
                    "recommendations_growth": 12.5,  # 推荐增长率（较上周）
                    "ctr_growth": 2.3,  # CTR增长率
                    "conversion_growth": -0.5,  # 转化率变化
                    "users_growth": 8.2,  # 用户增长率
                },
                "data_source": "simulated",  # 标记为模拟数据
                "message": "当前数据为模拟数据，生产环境需接入实时事件追踪系统"
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
            # 模拟24小时的趋势数据
            time_points = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
            
            # 模拟数据：实际应从事件日志按时间聚合
            trend_data = {
                "time_points": time_points,
                "metrics": {
                    "impressions": {  # 曝光数
                        "label": "推荐曝光",
                        "data": [12000, 8000, 15000, 28000, 32000, 28000, 18000],
                        "unit": "次"
                    },
                    "clicks": {  # 点击数
                        "label": "推荐点击",
                        "data": [2200, 1500, 2800, 5200, 6000, 5200, 3400],
                        "unit": "次"
                    },
                    "ctr": {  # 点击率
                        "label": "点击率",
                        "data": [18.3, 18.8, 18.7, 18.6, 18.8, 18.6, 18.9],
                        "unit": "%"
                    },
                    "conversions": {  # 转化数
                        "label": "转化数",
                        "data": [680, 450, 840, 1560, 1800, 1560, 1020],
                        "unit": "次"
                    }
                },
                "granularity": granularity,
                "data_source": "simulated"
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
            # 模拟用户行为数据
            behavior_data = {
                "user_metrics": {
                    "total_users": 52380,  # 总用户数
                    "active_users": 38650,  # 活跃用户数
                    "new_users": 4280,  # 新用户数
                    "returning_users": 34370,  # 回访用户数
                },
                "engagement": {
                    "avg_session_duration": 285,  # 平均会话时长（秒）
                    "avg_page_views": 12.5,  # 平均页面浏览数
                    "bounce_rate": 32.8,  # 跳出率（%）
                    "avg_recommendations_per_session": 8.3,  # 平均每次会话推荐数
                },
                "conversion_funnel": [
                    {"stage": "曝光", "users": 52380, "rate": 100.0},
                    {"stage": "点击", "users": 9743, "rate": 18.6},
                    {"stage": "查看详情", "users": 6820, "rate": 13.0},
                    {"stage": "加购", "users": 4186, "rate": 8.0},
                    {"stage": "下单", "users": 3038, "rate": 5.8},
                ],
                "top_behaviors": [
                    {"action": "浏览推荐", "count": 145680, "percentage": 45.2},
                    {"action": "点击推荐", "count": 87400, "percentage": 27.1},
                    {"action": "搜索", "count": 52340, "percentage": 16.2},
                    {"action": "收藏", "count": 23450, "percentage": 7.3},
                    {"action": "分享", "count": 13580, "percentage": 4.2},
                ],
                "data_source": "simulated"
            }
            
            return behavior_data
            
        except Exception as e:
            logger.error(f"获取用户行为分析失败: {e}")
            raise

