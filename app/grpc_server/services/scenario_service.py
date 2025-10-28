"""场景管理 gRPC 服务实现"""
import sys
from pathlib import Path

# 添加 grpc_generated 到 Python 路径
grpc_gen_path = Path(__file__).parent.parent.parent / "grpc_generated" / "python"
sys.path.insert(0, str(grpc_gen_path))

import grpc
from google.protobuf import struct_pb2
from google.protobuf import timestamp_pb2
from datetime import datetime
from typing import Dict, Any

from recommender.v1 import scenario_pb2, scenario_pb2_grpc
from recommender_common.v1 import pagination_pb2

from app.services.scenario.service import ScenarioService
from app.models.scenario import ScenarioCreate, ScenarioConfig, ScenarioUpdate


class ScenarioServicer(scenario_pb2_grpc.ScenarioServiceServicer):
    """场景管理 gRPC 服务"""
    
    def __init__(self, db):
        self.scenario_service = ScenarioService(db)
    
    async def CreateScenario(
        self, 
        request: scenario_pb2.CreateScenarioRequest,
        context: grpc.aio.ServicerContext
    ) -> scenario_pb2.CreateScenarioResponse:
        """创建场景"""
        try:
            # 转换 proto Struct 为 dict
            config_dict = self._struct_to_dict(request.config) if request.config else {}
            
            # 创建 ScenarioCreate 对象
            scenario_create = ScenarioCreate(
                scenario_id=request.scenario_id,
                scenario_type=request.scenario_type,
                name=request.name,
                description=request.description if request.description else None,
                config=ScenarioConfig(**config_dict) if config_dict else ScenarioConfig()
            )
            
            # 调用现有服务
            result = await self.scenario_service.create_scenario(
                tenant_id=request.tenant_id,
                data=scenario_create
            )
            
            # 转换为 proto message
            response = scenario_pb2.CreateScenarioResponse()
            self._dict_to_scenario_proto(result.model_dump(), response.scenario)
            
            return response
            
        except ValueError as e:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(str(e))
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            raise
    
    async def GetScenario(
        self,
        request: scenario_pb2.GetScenarioRequest,
        context: grpc.aio.ServicerContext
    ) -> scenario_pb2.GetScenarioResponse:
        """获取场景详情"""
        try:
            result = await self.scenario_service.get_scenario(
                request.tenant_id,
                request.scenario_id
            )
            
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("场景不存在")
                raise grpc.RpcError()
            
            response = scenario_pb2.GetScenarioResponse()
            self._dict_to_scenario_proto(result, response.scenario)
            
            return response
            
        except grpc.RpcError:
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"获取场景失败: {str(e)}")
            raise
    
    async def ListScenarios(
        self,
        request: scenario_pb2.ListScenariosRequest,
        context: grpc.aio.ServicerContext
    ) -> scenario_pb2.ListScenariosResponse:
        """查询场景列表"""
        try:
            # 调试日志
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"ListScenarios 收到请求: tenant_id={request.tenant_id}, status={request.status}")
            
            # 准备状态参数
            from app.models.scenario import ScenarioStatus
            status = None
            if request.status:
                try:
                    status = ScenarioStatus(request.status)
                except ValueError:
                    pass
            
            # 准备分页参数
            from app.models.base import PaginationParams
            pagination = None
            if request.HasField("page"):
                pagination = PaginationParams(
                    page=request.page.page,
                    page_size=request.page.page_size
                )
            
            # 调用服务
            scenarios, total = await self.scenario_service.list_scenarios(
                tenant_id=request.tenant_id,
                status=status,
                pagination=pagination
            )
            
            logger.info(f"查询到 {len(scenarios)} 条场景, 总数: {total}")
            
            # 构建响应
            response = scenario_pb2.ListScenariosResponse()
            
            for scenario in scenarios:
                scenario_proto = response.scenarios.add()
                self._dict_to_scenario_proto(scenario.model_dump(), scenario_proto)
            
            # 设置分页信息
            page = request.page.page if request.HasField("page") else 1
            page_size = request.page.page_size if request.HasField("page") else 20
            total_pages = (total + page_size - 1) // page_size
            
            response.page_info.page = page
            response.page_info.page_size = page_size
            response.page_info.total = total
            response.page_info.total_pages = total_pages
            response.page_info.has_next = page < total_pages
            response.page_info.has_prev = page > 1
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"查询场景列表失败: {str(e)}")
            raise
    
    async def UpdateScenario(
        self,
        request: scenario_pb2.UpdateScenarioRequest,
        context: grpc.aio.ServicerContext
    ) -> scenario_pb2.UpdateScenarioResponse:
        """更新场景"""
        try:
            # 准备更新数据
            update_dict = {}
            if request.name:
                update_dict["name"] = request.name
            if request.description:
                update_dict["description"] = request.description
            if request.config:
                config_dict = self._struct_to_dict(request.config)
                update_dict["config"] = ScenarioConfig(**config_dict)
            
            # 创建 ScenarioUpdate 对象
            scenario_update = ScenarioUpdate(**update_dict)
            
            # 调用服务
            result = await self.scenario_service.update_scenario(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                data=scenario_update
            )
            
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("场景不存在")
                raise grpc.RpcError()
            
            # 构建响应
            response = scenario_pb2.UpdateScenarioResponse()
            self._dict_to_scenario_proto(result.model_dump(), response.scenario)
            
            return response
            
        except grpc.RpcError:
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"更新场景失败: {str(e)}")
            raise
    
    async def DeleteScenario(
        self,
        request: scenario_pb2.DeleteScenarioRequest,
        context: grpc.aio.ServicerContext
    ) -> scenario_pb2.DeleteScenarioResponse:
        """删除场景"""
        try:
            await self.scenario_service.delete_scenario(
                request.tenant_id,
                request.scenario_id
            )
            
            return scenario_pb2.DeleteScenarioResponse(success=True)
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"删除场景失败: {str(e)}")
            raise
    
    async def UpdateScenarioStatus(
        self,
        request: scenario_pb2.UpdateScenarioStatusRequest,
        context: grpc.aio.ServicerContext
    ) -> scenario_pb2.UpdateScenarioStatusResponse:
        """更新场景状态"""
        try:
            from app.models.scenario import ScenarioStatus
            
            # 创建 ScenarioUpdate 对象
            scenario_update = ScenarioUpdate(
                status=ScenarioStatus(request.status)
            )
            
            # 调用服务
            result = await self.scenario_service.update_scenario(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                data=scenario_update
            )
            
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("场景不存在")
                raise grpc.RpcError()
            
            response = scenario_pb2.UpdateScenarioStatusResponse()
            self._dict_to_scenario_proto(result.model_dump(), response.scenario)
            
            return response
            
        except grpc.RpcError:
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"更新场景状态失败: {str(e)}")
            raise
    
    # 辅助方法
    
    def _dict_to_scenario_proto(self, data: Dict[str, Any], scenario: scenario_pb2.Scenario):
        """将 dict 转换为 Scenario proto message"""
        scenario.id = str(data.get("_id", ""))
        scenario.tenant_id = data.get("tenant_id", "")
        scenario.scenario_id = data.get("scenario_id", "")
        scenario.name = data.get("name", "")
        scenario.scenario_type = data.get("scenario_type", "")
        scenario.description = data.get("description", "")
        scenario.status = data.get("status", "active")
        
        # 转换 config
        if "config" in data and data["config"]:
            self._dict_to_struct(data["config"], scenario.config)
        
        # 转换时间
        if "created_at" in data and data["created_at"]:
            self._datetime_to_timestamp(data["created_at"], scenario.created_at)
        if "updated_at" in data and data["updated_at"]:
            self._datetime_to_timestamp(data["updated_at"], scenario.updated_at)
    
    def _struct_to_dict(self, struct: struct_pb2.Struct) -> Dict:
        """将 proto Struct 转换为 dict"""
        import json
        return json.loads(struct_pb2.Struct.to_json(struct))
    
    def _dict_to_struct(self, data: Dict, struct: struct_pb2.Struct):
        """将 dict 转换为 proto Struct"""
        import json
        struct.update(json.loads(json.dumps(data)))
    
    def _datetime_to_timestamp(self, dt: datetime, ts: timestamp_pb2.Timestamp):
        """将 datetime 转换为 proto Timestamp"""
        ts.FromDatetime(dt)
    
    def _set_page_info(self, page_data: Dict, page_info: pagination_pb2.PageInfo):
        """设置分页信息"""
        page_info.page = page_data.get("page", 1)
        page_info.page_size = page_data.get("page_size", 20)
        page_info.total = page_data.get("total", 0)
        page_info.total_pages = page_data.get("total_pages", 0)
        page_info.has_next = page_data.get("has_next", False)
        page_info.has_prev = page_data.get("has_prev", False)

