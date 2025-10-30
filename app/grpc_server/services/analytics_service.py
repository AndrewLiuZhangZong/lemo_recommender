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
            
            # 填充dashboard数据
            response.data.total_recommendations = dashboard_data["overview"]["total_recommendations"]
            response.data.total_clicks = int(dashboard_data["overview"]["total_recommendations"] * dashboard_data["overview"]["ctr"] / 100)
            response.data.ctr = dashboard_data["overview"]["ctr"]
            response.data.total_users = dashboard_data["overview"]["active_users"] * 2  # 估算总用户数
            response.data.active_users = dashboard_data["overview"]["active_users"]
            response.data.total_items = dashboard_data["overview"]["total_items"]
            response.data.avg_response_time = 50.5  # 模拟数据
            response.data.cache_hit_rate = 85.3  # 模拟数据
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def GetMetricsTrend(self, request, context):
        """获取指标趋势"""
        try:
            from google.protobuf import timestamp_pb2
            from datetime import datetime, timedelta
            
            # 获取指标趋势数据
            trend_data = await self.analytics_service.get_metrics_trend(
                tenant_id=request.tenant_id,
                metrics=list(request.metrics) if request.metrics else ["impressions", "clicks", "ctr"],
                scenario_id=request.scenario_id if request.scenario_id else None,
                granularity=request.granularity if request.granularity else "hour"
            )
            
            # 构建响应
            response = analytics_pb2.GetMetricsTrendResponse()
            
            # 生成时间戳（模拟最近24小时）
            now = datetime.utcnow()
            timestamps = [now - timedelta(hours=24-i*4) for i in range(7)]
            
            # 填充各个指标数据
            for metric_key, metric_info in trend_data["metrics"].items():
                metric_trend = response.trends.add()
                metric_trend.metric_name = metric_key
                
                # 为每个数据点创建时间序列
                for i, value in enumerate(metric_info["data"]):
                    point = metric_trend.points.add()
                    ts = timestamp_pb2.Timestamp()
                    ts.FromDatetime(timestamps[i])
                    point.timestamp.CopyFrom(ts)
                    point.value = float(value)
            
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
            
            # 计算总数用于计算百分比
            total = sum(item["value"] for item in distribution["items"])
            
            # 填充分布项
            for item in distribution["items"]:
                dist_item = response.distribution.add()
                dist_item.label = item["name"]
                dist_item.count = item["value"]
                dist_item.percentage = (item["value"] / total * 100) if total > 0 else 0.0
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def GetUserBehaviorAnalysis(self, request, context):
        """获取用户行为分析"""
        try:
            from google.protobuf import struct_pb2
            
            # 获取用户行为分析数据
            behavior_data = await self.analytics_service.get_user_behavior_analysis(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id if request.scenario_id else None
            )
            
            # 构建响应
            response = analytics_pb2.GetUserBehaviorAnalysisResponse()
            
            # 填充行为统计（根据protobuf定义：action_type, count, unique_users）
            for behavior_item in behavior_data["top_behaviors"]:
                stat = response.stats.add()
                stat.action_type = behavior_item["action"]
                stat.count = behavior_item["count"]
                # 估算独立用户数（假设平均每用户2次行为）
                stat.unique_users = behavior_item["count"] // 2
            
            # 填充漏斗数据（使用JSON格式）
            funnel_dict = {
                "user_metrics": behavior_data["user_metrics"],
                "engagement": behavior_data["engagement"],
                "conversion_funnel": behavior_data["conversion_funnel"]
            }
            
            # 转换为protobuf Struct
            funnel_struct = struct_pb2.Struct()
            funnel_struct.update(funnel_dict)
            response.funnel_data.CopyFrom(funnel_struct)
            
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
