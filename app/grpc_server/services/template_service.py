"""
模板管理 gRPC 服务实现
"""
import logging
import grpc
from google.protobuf import struct_pb2, timestamp_pb2
from google.protobuf.json_format import MessageToDict

from recommender.v1 import template_pb2, template_pb2_grpc
from recommender_common.v1 import pagination_pb2
from app.services.template.service import TemplateService
from app.models.template import TemplateCreate, TemplateUpdate
from app.models.base import PaginationParams

logger = logging.getLogger(__name__)


class TemplateServicer(template_pb2_grpc.TemplateServiceServicer):
    """模板管理服务实现"""
    
    def __init__(self, db):
        self.template_service = TemplateService(db["config_templates"])
    
    def _struct_to_dict(self, struct_data: struct_pb2.Struct) -> dict:
        """将 protobuf Struct 转换为 Python dict"""
        return MessageToDict(struct_data)
    
    def _dict_to_struct(self, data: dict) -> struct_pb2.Struct:
        """将 Python dict 转换为 protobuf Struct"""
        struct = struct_pb2.Struct()
        struct.update(data)
        return struct
    
    def _dict_to_template_proto(self, data: dict, template_msg: template_pb2.Template):
        """将字典转换为 protobuf Template 消息"""
        template_msg.id = str(data.get("_id", ""))
        template_msg.template_id = data.get("template_id", "")
        template_msg.name = data.get("name", "")
        template_msg.description = data.get("description", "")
        template_msg.scenario_types.extend(data.get("scenario_types", []))
        
        if data.get("config"):
            template_msg.config.CopyFrom(self._dict_to_struct(data["config"]))
        
        template_msg.is_system = data.get("is_system", False)
        template_msg.creator = data.get("creator", "")
        
        # 时间戳
        if data.get("created_at"):
            ts = timestamp_pb2.Timestamp()
            ts.FromDatetime(data["created_at"])
            template_msg.created_at.CopyFrom(ts)
        
        if data.get("updated_at"):
            ts = timestamp_pb2.Timestamp()
            ts.FromDatetime(data["updated_at"])
            template_msg.updated_at.CopyFrom(ts)
    
    async def CreateTemplate(self, request, context):
        """创建模板"""
        try:
            logger.info(f"创建模板: template_id={request.template_id}, name={request.name}")
            
            # 转换配置
            config_dict = self._struct_to_dict(request.config) if request.config else {}
            
            # 构建创建对象
            template_create = TemplateCreate(
                template_id=request.template_id,
                name=request.name,
                description=request.description if request.description else "",
                scenario_types=list(request.scenario_types) if request.scenario_types else [],
                config=config_dict,
                creator=request.creator if request.creator else ""
            )
            
            # 创建模板
            result = await self.template_service.create_template(template_create)
            
            # 构建响应
            response = template_pb2.CreateTemplateResponse()
            self._dict_to_template_proto(result.model_dump(), response.template)
            
            logger.info(f"模板创建成功: template_id={request.template_id}")
            return response
        
        except ValueError as e:
            logger.error(f"创建模板失败: {e}")
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(str(e))
            return template_pb2.CreateTemplateResponse()
        except Exception as e:
            logger.error(f"创建模板异常: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            return template_pb2.CreateTemplateResponse()
    
    async def GetTemplate(self, request, context):
        """获取模板详情"""
        try:
            logger.info(f"获取模板: template_id={request.template_id}")
            
            result = await self.template_service.get_template(request.template_id)
            
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"模板不存在: {request.template_id}")
                return template_pb2.GetTemplateResponse()
            
            response = template_pb2.GetTemplateResponse()
            self._dict_to_template_proto(result.model_dump(), response.template)
            
            return response
        
        except Exception as e:
            logger.error(f"获取模板异常: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            return template_pb2.GetTemplateResponse()
    
    async def ListTemplates(self, request, context):
        """查询模板列表"""
        try:
            logger.info(f"查询模板列表: scenario_type={request.scenario_type}, is_system={request.is_system}")
            
            # 构建分页参数
            pagination = None
            if request.page:
                pagination = PaginationParams(
                    page=request.page.page,
                    page_size=request.page.page_size
                )
            
            # 查询
            scenario_type = request.scenario_type if request.scenario_type else None
            is_system = request.is_system if request.HasField("is_system") else None
            
            templates, total = await self.template_service.list_templates(
                scenario_type=scenario_type,
                is_system=is_system,
                pagination=pagination
            )
            
            # 构建响应
            response = template_pb2.ListTemplatesResponse()
            
            for template in templates:
                template_msg = response.templates.add()
                self._dict_to_template_proto(template.model_dump(), template_msg)
            
            # 分页信息
            if pagination:
                response.page_info.page = pagination.page
                response.page_info.page_size = pagination.page_size
                response.page_info.total = total
            
            logger.info(f"查询到 {len(templates)} 个模板, 总数: {total}")
            return response
        
        except Exception as e:
            logger.error(f"查询模板列表异常: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            return template_pb2.ListTemplatesResponse()
    
    async def UpdateTemplate(self, request, context):
        """更新模板"""
        try:
            logger.info(f"更新模板: template_id={request.template_id}")
            
            # 构建更新对象
            update_data = {}
            if request.name:
                update_data["name"] = request.name
            if request.description:
                update_data["description"] = request.description
            if request.scenario_types:
                update_data["scenario_types"] = list(request.scenario_types)
            if request.config:
                update_data["config"] = self._struct_to_dict(request.config)
            
            template_update = TemplateUpdate(**update_data)
            
            # 更新
            result = await self.template_service.update_template(
                template_id=request.template_id,
                data=template_update
            )
            
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"模板不存在: {request.template_id}")
                return template_pb2.UpdateTemplateResponse()
            
            # 构建响应
            response = template_pb2.UpdateTemplateResponse()
            self._dict_to_template_proto(result.model_dump(), response.template)
            
            logger.info(f"模板更新成功: template_id={request.template_id}")
            return response
        
        except Exception as e:
            logger.error(f"更新模板异常: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            return template_pb2.UpdateTemplateResponse()
    
    async def DeleteTemplate(self, request, context):
        """删除模板"""
        try:
            logger.info(f"删除模板: template_id={request.template_id}")
            
            success = await self.template_service.delete_template(request.template_id)
            
            response = template_pb2.DeleteTemplateResponse()
            response.success = success
            
            if success:
                logger.info(f"模板删除成功: template_id={request.template_id}")
            else:
                logger.warning(f"模板删除失败: template_id={request.template_id}")
            
            return response
        
        except ValueError as e:
            logger.error(f"删除模板失败: {e}")
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details(str(e))
            return template_pb2.DeleteTemplateResponse()
        except Exception as e:
            logger.error(f"删除模板异常: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            return template_pb2.DeleteTemplateResponse()
    
    async def GetTemplateByScenarioType(self, request, context):
        """根据场景类型获取推荐模板"""
        try:
            logger.info(f"根据场景类型获取模板: scenario_type={request.scenario_type}")
            
            result = await self.template_service.get_template_by_scenario_type(
                scenario_type=request.scenario_type
            )
            
            if not result:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"未找到适用于 {request.scenario_type} 的模板")
                return template_pb2.GetTemplateByScenarioTypeResponse()
            
            response = template_pb2.GetTemplateByScenarioTypeResponse()
            self._dict_to_template_proto(result.model_dump(), response.template)
            
            logger.info(f"找到模板: template_id={result.template_id}")
            return response
        
        except Exception as e:
            logger.error(f"获取推荐模板异常: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected {type(e).__name__}: {str(e)}")
            return template_pb2.GetTemplateByScenarioTypeResponse()

