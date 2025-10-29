"""AB实验 gRPC 服务实现（简化版）"""
import sys
from pathlib import Path

grpc_gen_path = Path(__file__).parent.parent.parent / "grpc_generated" / "python"
sys.path.insert(0, str(grpc_gen_path))

import grpc
from recommender.v1 import experiment_pb2, experiment_pb2_grpc
from app.services.experiment.service import ExperimentService
from .base_service import BaseServicer


class ExperimentServicer(experiment_pb2_grpc.ExperimentServiceServicer, BaseServicer):
    """AB实验 gRPC 服务（简化实现）"""
    
    def __init__(self, db):
        self.experiment_service = ExperimentService(db)
    
    async def CreateExperiment(self, request, context):
        """创建实验"""
        try:
            from app.models.experiment import Experiment, ExperimentVariant, ExperimentMetrics
            from bson import ObjectId
            
            # 自动生成 experiment_id
            experiment_id = str(ObjectId())
            
            # 转换variants（支持新的结构化策略配置）
            variants = []
            for group in request.groups:
                # 解析策略配置
                variant_config = {}
                if group.HasField("strategy"):
                    variant_config = {
                        "recall_model_ids": list(group.strategy.recall_model_ids),
                        "rank_model_id": group.strategy.rank_model_id,
                        "rerank_rule_ids": list(group.strategy.rerank_rule_ids),
                    }
                
                variants.append(ExperimentVariant(
                    variant_id=group.group_id,
                    name=group.name,
                    traffic_percentage=group.traffic_ratio * 100.0,  # 转回百分比
                    config=variant_config
                ))
            
            # 解析流量分配方法
            from app.models.experiment import TrafficSplitMethod
            traffic_split_method = TrafficSplitMethod.USER_ID_HASH  # 默认值
            if request.traffic_split_method == 1:
                traffic_split_method = TrafficSplitMethod.USER_ID_HASH
            elif request.traffic_split_method == 2:
                traffic_split_method = TrafficSplitMethod.RANDOM
            elif request.traffic_split_method == 3:
                traffic_split_method = TrafficSplitMethod.WEIGHTED
            
            # 构建Experiment对象（包含所有业界标准字段）
            experiment = Experiment(
                experiment_id=experiment_id,
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                name=request.name,
                description=request.description if request.description else "",
                hypothesis=request.hypothesis if request.hypothesis else "",
                variants=variants,
                traffic_split_method=traffic_split_method,
                metrics=ExperimentMetrics(
                    primary_metric="ctr",  # 默认值
                    secondary_metrics=[],
                    guardrail_metrics=[]
                ),
                min_sample_size=request.min_sample_size if request.min_sample_size else 1000,
                confidence_level=request.confidence_level if request.confidence_level else 0.95,
                created_by=request.created_by if request.created_by else "system"
            )
            
            # 调用服务创建
            result = await self.experiment_service.create_experiment(experiment)
            
            # 构建响应
            response = experiment_pb2.CreateExperimentResponse()
            self._dict_to_experiment_proto(result.model_dump(), response.experiment)
            
            return response
            
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def GetExperiment(self, request, context):
        """获取实验详情"""
        try:
            result = await self.experiment_service.get_experiment(
                tenant_id=request.tenant_id,
                experiment_id=request.experiment_id
            )
            
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("实验不存在")
                raise grpc.RpcError()
            
            response = experiment_pb2.GetExperimentResponse()
            self._dict_to_experiment_proto(result.model_dump(), response.experiment)
            return response
            
        except grpc.RpcError:
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def ListExperiments(self, request, context):
        """查询实验列表"""
        try:
            from app.models.experiment import ExperimentStatus
            
            # 解析状态
            status = None
            if request.status and request.status != 0:  # 0是UNSPECIFIED
                # protobuf enum转Python enum
                status_map = {
                    1: ExperimentStatus.DRAFT,
                    2: ExperimentStatus.RUNNING,
                    3: ExperimentStatus.PAUSED,
                    4: ExperimentStatus.COMPLETED,
                    5: ExperimentStatus.ARCHIVED,
                }
                status = status_map.get(request.status)
            
            # 调用服务
            experiments = await self.experiment_service.list_experiments(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id if request.scenario_id else None,
                status=status
            )
            
            # 构建响应
            response = experiment_pb2.ListExperimentsResponse()
            for exp in experiments:
                exp_proto = response.experiments.add()
                self._dict_to_experiment_proto(exp.model_dump(), exp_proto)
            
            # 设置分页信息
            if request.HasField("page"):
                response.page_info.page = request.page.page
                response.page_info.page_size = request.page.page_size
                response.page_info.total = len(experiments)
                response.page_info.total_pages = 1
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def UpdateExperiment(self, request, context):
        """更新实验"""
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
    
    async def DeleteExperiment(self, request, context):
        """删除实验"""
        try:
            # 软删除：更新状态为archived
            result = await self.experiment_service.delete_experiment(
                tenant_id=request.tenant_id,
                experiment_id=request.experiment_id,
                soft_delete=True
            )
            
            response = experiment_pb2.DeleteExperimentResponse()
            response.success = result
            return response
            
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def StartExperiment(self, request, context):
        """启动实验"""
        try:
            result = await self.experiment_service.start_experiment(
                tenant_id=request.tenant_id,
                experiment_id=request.experiment_id
            )
            
            response = experiment_pb2.StartExperimentResponse()
            self._dict_to_experiment_proto(result.model_dump(), response.experiment)
            return response
            
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def StopExperiment(self, request, context):
        """停止实验"""
        try:
            result = await self.experiment_service.stop_experiment(
                tenant_id=request.tenant_id,
                experiment_id=request.experiment_id
            )
            
            response = experiment_pb2.StopExperimentResponse()
            self._dict_to_experiment_proto(result.model_dump(), response.experiment)
            return response
            
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def GetExperimentResults(self, request, context):
        """获取实验结果"""
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
    
    def _dict_to_experiment_proto(self, data: dict, proto):
        """将字典转换为experiment protobuf对象"""
        from google.protobuf import timestamp_pb2
        import json
        
        # 基本字段
        proto.experiment_id = data.get("experiment_id", "")
        proto.tenant_id = data.get("tenant_id", "")
        proto.scenario_id = data.get("scenario_id", "")
        proto.name = data.get("name", "")
        proto.description = data.get("description", "")
        proto.hypothesis = data.get("hypothesis", "")
        
        # 状态映射
        status_str = data.get("status", "draft")
        status_map = {
            "draft": 1,
            "running": 2,
            "paused": 3,
            "completed": 4,
            "archived": 5,
        }
        proto.status = status_map.get(status_str, 1)
        
        # 时间字段
        for time_field in ["start_time", "end_time", "created_at", "updated_at"]:
            if time_field in data and data[time_field]:
                ts = timestamp_pb2.Timestamp()
                if isinstance(data[time_field], str):
                    from datetime import datetime
                    dt = datetime.fromisoformat(data[time_field].replace('Z', '+00:00'))
                    ts.FromDatetime(dt)
                else:
                    ts.FromDatetime(data[time_field])
                getattr(proto, time_field).CopyFrom(ts)
        
        # variants (ExperimentGroup in proto)
        if "variants" in data and data["variants"]:
            for variant in data["variants"]:
                group = proto.groups.add()
                group.group_id = variant.get("variant_id", "")
                group.name = variant.get("name", "")
                group.traffic_ratio = variant.get("traffic_percentage", 0.0) / 100.0
                
                # config - 转换为JSON字符串或Struct
                if "config" in variant:
                    from google.protobuf import struct_pb2
                    config_struct = struct_pb2.Struct()
                    config_struct.update(variant["config"])
                    group.config.CopyFrom(config_struct)
        
        # created_by
        proto.created_by = data.get("created_by", "")

