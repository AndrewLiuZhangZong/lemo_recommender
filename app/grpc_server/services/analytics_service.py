"""数据分析 gRPC 服务实现"""
import sys
from pathlib import Path

grpc_gen_path = Path(__file__).parent.parent.parent / "grpc_generated" / "python"
sys.path.insert(0, str(grpc_gen_path))

import grpc
from recommender.v1 import analytics_pb2, analytics_pb2_grpc
from .base_service import BaseServicer
from app.services.analytics import AnalyticsService


class AnalyticsServicer(analytics_pb2_grpc.AnalyticsServiceServicer, BaseServicer):
    """数据分析 gRPC 服务"""
    
    def __init__(self, db):
        self.db = db
        self.analytics_service = AnalyticsService(db)
    
    async def GetDashboard(self, request, context):
        """获取仪表板数据"""
        try:
            # 获取仪表板数据
            dashboard_data = await self.analytics_service.get_dashboard_data(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id if request.scenario_id else None
            )
            
            # 构建响应
            response = analytics_pb2.GetDashboardResponse()
            
            # 填充概览数据
            overview = response.overview
            overview.total_recommendations = dashboard_data["overview"]["total_recommendations"]
            overview.ctr = dashboard_data["overview"]["ctr"]
            overview.conversion_rate = dashboard_data["overview"]["conversion_rate"]
            overview.active_users = dashboard_data["overview"]["active_users"]
            overview.total_items = dashboard_data["overview"]["total_items"]
            overview.active_scenarios = dashboard_data["overview"]["active_scenarios"]
            overview.running_experiments = dashboard_data["overview"]["running_experiments"]
            
            # 填充趋势数据
            trend = response.trend
            trend.recommendations_growth = dashboard_data["trend"]["recommendations_growth"]
            trend.ctr_growth = dashboard_data["trend"]["ctr_growth"]
            trend.conversion_growth = dashboard_data["trend"]["conversion_growth"]
            trend.users_growth = dashboard_data["trend"]["users_growth"]
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def GetMetricsTrend(self, request, context):
        """获取指标趋势"""
        try:
            # 获取指标趋势数据
            trend_data = await self.analytics_service.get_metrics_trend(
                tenant_id=request.tenant_id,
                metrics=list(request.metrics) if request.metrics else ["impressions", "clicks", "ctr"],
                scenario_id=request.scenario_id if request.scenario_id else None,
                granularity=request.granularity if request.granularity else "hour"
            )
            
            # 构建响应
            response = analytics_pb2.GetMetricsTrendResponse()
            response.time_points.extend(trend_data["time_points"])
            
            # 填充各个指标数据
            for metric_key, metric_info in trend_data["metrics"].items():
                metric_data = response.metrics.add()
                metric_data.metric_name = metric_key
                metric_data.label = metric_info["label"]
                metric_data.unit = metric_info["unit"]
                metric_data.values.extend([float(v) for v in metric_info["data"]])
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def GetItemDistribution(self, request, context):
        """获取物品分布统计"""
        try:
            # 获取物品分布数据
            distribution = await self.analytics_service.get_item_distribution(
                tenant_id=request.tenant_id,
                dimension=request.dimension if request.dimension else "scenario",
                scenario_id=request.scenario_id if request.scenario_id else None
            )
            
            # 构建响应
            response = analytics_pb2.GetItemDistributionResponse()
            response.dimension = distribution["dimension"]
            
            # 填充分布项
            for item in distribution["items"]:
                dist_item = response.items.add()
                dist_item.name = item["name"]
                dist_item.value = item["value"]
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def GetUserBehaviorAnalysis(self, request, context):
        """获取用户行为分析"""
        try:
            # 获取用户行为分析数据
            behavior_data = await self.analytics_service.get_user_behavior_analysis(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id if request.scenario_id else None
            )
            
            # 构建响应
            response = analytics_pb2.GetUserBehaviorAnalysisResponse()
            
            # 填充用户指标
            user_metrics = response.user_metrics
            user_metrics.total_users = behavior_data["user_metrics"]["total_users"]
            user_metrics.active_users = behavior_data["user_metrics"]["active_users"]
            user_metrics.new_users = behavior_data["user_metrics"]["new_users"]
            user_metrics.returning_users = behavior_data["user_metrics"]["returning_users"]
            
            # 填充参与度指标
            engagement = response.engagement
            engagement.avg_session_duration = behavior_data["engagement"]["avg_session_duration"]
            engagement.avg_page_views = behavior_data["engagement"]["avg_page_views"]
            engagement.bounce_rate = behavior_data["engagement"]["bounce_rate"]
            engagement.avg_recommendations_per_session = behavior_data["engagement"]["avg_recommendations_per_session"]
            
            # 填充转化漏斗
            for funnel_item in behavior_data["conversion_funnel"]:
                funnel = response.conversion_funnel.add()
                funnel.stage = funnel_item["stage"]
                funnel.users = funnel_item["users"]
                funnel.rate = funnel_item["rate"]
            
            # 填充热门行为
            for behavior_item in behavior_data["top_behaviors"]:
                behavior = response.top_behaviors.add()
                behavior.action = behavior_item["action"]
                behavior.count = behavior_item["count"]
                behavior.percentage = behavior_item["percentage"]
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def ExportData(self, request, context):
        """导出数据"""
        try:
            context.set_code(grpc.StatusCode.UNIMPLEMENTED)
            context.set_details("功能待实现")
            raise grpc.RpcError()
        except grpc.RpcError:
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            raise
