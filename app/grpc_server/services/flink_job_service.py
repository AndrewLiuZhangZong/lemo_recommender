"""
Flink 作业管理 gRPC 服务实现
"""
import sys
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from google.protobuf import struct_pb2, timestamp_pb2
from google.protobuf.json_format import MessageToDict, ParseDict
from grpc import StatusCode
import grpc

# 添加 grpc_generated 到 Python 路径
grpc_gen_path = Path(__file__).parent.parent.parent / "grpc_generated" / "python"
sys.path.insert(0, str(grpc_gen_path))

try:
    from recommender.v1 import flink_job_pb2, flink_job_pb2_grpc
    from recommender_common.v1 import pagination_pb2
except ImportError:
    # Proto 文件还未生成，使用占位符
    flink_job_pb2 = None
    flink_job_pb2_grpc = None

from app.services.flink import get_flink_job_manager
from app.models.flink_job_template import (
    JobTemplateCreate, FlinkJobSubmitRequest, JobTemplateType, JobStatus
)


class FlinkJobServicer(flink_job_pb2_grpc.FlinkJobServiceServicer):
    """Flink 作业管理 gRPC 服务"""
    
    def __init__(self):
        if flink_job_pb2_grpc is None:
            raise ImportError("Flink job proto 文件未生成，请先运行 make generate")
        super().__init__()
        self.job_manager = get_flink_job_manager()
    
    def _dict_to_struct(self, data: Dict[str, Any]) -> struct_pb2.Struct:
        """将 dict 转换为 proto Struct"""
        struct = struct_pb2.Struct()
        struct.update(data)
        return struct
    
    def _struct_to_dict(self, struct: struct_pb2.Struct) -> Dict[str, Any]:
        """将 proto Struct 转换为 dict"""
        return MessageToDict(struct)
    
    def _datetime_to_timestamp(self, dt: datetime) -> timestamp_pb2.Timestamp:
        """将 datetime 转换为 proto Timestamp"""
        ts = timestamp_pb2.Timestamp()
        if dt:
            ts.FromDatetime(dt)
        return ts
    
    
    async def CreateJobTemplate(
        self,
        request: "flink_job_pb2.CreateJobTemplateRequest",
        context
    ) -> "flink_job_pb2.CreateJobTemplateResponse":
        """创建作业模板"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 转换 job_type 枚举
            # Proto 枚举可能是枚举对象（有 .name 属性）或整数（枚举值）
            if hasattr(request.job_type, 'name'):
                # 是枚举对象
                job_type_name = request.job_type.name
            else:
                # 是整数，需要从 proto 枚举中查找
                job_type_value = int(request.job_type)
                # 从 proto 枚举中查找对应的枚举名
                job_type_enum_name_map = {
                    0: "JOB_TEMPLATE_TYPE_UNSPECIFIED",
                    1: "PYTHON_SCRIPT",
                    2: "JAR",
                    3: "SQL",
                    4: "PYTHON_FLINK",
                }
                job_type_name = job_type_enum_name_map.get(job_type_value)
                if not job_type_name:
                    logger.error(f"无效的作业类型值: {job_type_value}")
                    context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                    context.set_details(f"无效的作业类型值: {job_type_value}")
                    raise ValueError(f"无效的作业类型值: {job_type_value}")
            
            # 映射关系：Proto 枚举名（大写）-> Python 枚举（小写值）
            type_mapping = {
                "PYTHON_SCRIPT": JobTemplateType.PYTHON_SCRIPT,
                "JAR": JobTemplateType.JAR,
                "SQL": JobTemplateType.SQL,
                "PYTHON_FLINK": JobTemplateType.PYTHON_FLINK,
            }
            
            job_type_enum = type_mapping.get(job_type_name)
            if not job_type_enum:
                logger.error(f"无效的作业类型: {job_type_name}")
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(f"无效的作业类型: {job_type_name}")
                raise ValueError(f"无效的作业类型: {job_type_name}")
            
            # 转换请求
            template_data = JobTemplateCreate(
                template_id=request.template_id,
                name=request.name,
                description=request.description if request.description else None,
                job_type=job_type_enum,
                config=self._struct_to_dict(request.config) if request.config else {},
                parallelism=request.parallelism,
                checkpoints_enabled=request.checkpoints_enabled,
                checkpoint_interval_ms=request.checkpoint_interval_ms,
                task_manager_memory=request.task_manager_memory if request.task_manager_memory else "1024m",
                job_manager_memory=request.job_manager_memory if request.job_manager_memory else "512m",
                tags=list(request.tags) if request.tags else []
            )
            
            logger.info(f"创建作业模板: {template_data.template_id}, name={template_data.name}, job_type={job_type_name}")
            
            # 调用服务
            template = await self.job_manager.create_job_template(template_data)
            
            logger.info(f"作业模板创建成功: {template.template_id}")
            
            # 构建响应
            template_pb = flink_job_pb2.JobTemplate(
                template_id=template.template_id,
                name=template.name,
                description=template.description or "",
                job_type=getattr(flink_job_pb2.JobTemplateType, template.job_type.name),
                config=self._dict_to_struct(template.config) if template.config else self._dict_to_struct({}),
                parallelism=template.parallelism,
                checkpoints_enabled=template.checkpoints_enabled,
                checkpoint_interval_ms=template.checkpoint_interval_ms or 0,
                task_manager_memory=template.task_manager_memory or "",
                job_manager_memory=template.job_manager_memory or "",
                status=template.status or "active",
                tags=template.tags or [],
                created_by=template.created_by or "",
                created_at=self._datetime_to_timestamp(template.created_at) if template.created_at else None,
                updated_at=self._datetime_to_timestamp(template.updated_at) if template.updated_at else None
            )
            
            return flink_job_pb2.CreateJobTemplateResponse(
                template=template_pb
            )
        
        except ValueError as e:
            # 参数错误，已经在上面设置了 context
            logger.error(f"创建作业模板失败（参数错误）: {e}")
            raise
        except Exception as e:
            logger.error(f"创建作业模板失败: {e}", exc_info=True)
            if context.code() == grpc.StatusCode.OK:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"创建作业模板失败: {str(e)}")
            raise
    
    async def GetJobTemplate(
        self,
        request: "flink_job_pb2.GetJobTemplateRequest",
        context
    ) -> "flink_job_pb2.GetJobTemplateResponse":
        """获取作业模板"""
        try:
            template = await self.job_manager.get_job_template(request.template_id)
            
            if not template:
                return flink_job_pb2.GetJobTemplateResponse(
                    template=None
                )
            
            # 转换为 proto
            template_pb = flink_job_pb2.JobTemplate(
                template_id=template.template_id,
                name=template.name,
                description=template.description or "",
                job_type=getattr(flink_job_pb2, template.job_type.name),
                config=self._dict_to_struct(template.config),
                parallelism=template.parallelism,
                checkpoints_enabled=template.checkpoints_enabled,
                checkpoint_interval_ms=template.checkpoint_interval_ms,
                task_manager_memory=template.task_manager_memory,
                job_manager_memory=template.job_manager_memory,
                status=template.status,
                tags=template.tags,
                created_by=template.created_by or "",
                created_at=self._datetime_to_timestamp(template.created_at),
                updated_at=self._datetime_to_timestamp(template.updated_at)
            )
            
            return flink_job_pb2.GetJobTemplateResponse(
                template=template_pb
            )
        
        except Exception as e:
            return flink_job_pb2.GetJobTemplateResponse(
                template=None
            )
    
    async def ListJobTemplates(
        self,
        request: "flink_job_pb2.ListJobTemplatesRequest",
        context
    ) -> "flink_job_pb2.ListJobTemplatesResponse":
        """列出作业模板"""
        try:
            templates = await self.job_manager.list_job_templates(status=request.status if request.status else None)
            
            # 转换为 proto
            templates_pb = []
            for template in templates:
                template_pb = flink_job_pb2.JobTemplate(
                    template_id=template.template_id,
                    name=template.name,
                    description=template.description or "",
                    job_type=getattr(flink_job_pb2, template.job_type.name),
                    config=self._dict_to_struct(template.config),
                    parallelism=template.parallelism,
                    checkpoints_enabled=template.checkpoints_enabled,
                    checkpoint_interval_ms=template.checkpoint_interval_ms,
                    task_manager_memory=template.task_manager_memory,
                    job_manager_memory=template.job_manager_memory,
                    status=template.status,
                    tags=template.tags,
                    created_by=template.created_by or "",
                    created_at=self._datetime_to_timestamp(template.created_at),
                    updated_at=self._datetime_to_timestamp(template.updated_at)
                )
                templates_pb.append(template_pb)
            
            return flink_job_pb2.ListJobTemplatesResponse(
                
                templates=templates_pb,
                page_info=pagination_pb2.PageInfo(
                    page=request.page,
                    page_size=request.page_size,
                    total=len(templates),
                    total_pages=(len(templates) + request.page_size - 1) // request.page_size
                )
            )
        
        except Exception as e:
            return flink_job_pb2.ListJobTemplatesResponse(
                templates=[],
                page_info=pagination_pb2.PageInfo()
            )
    
    async def SubmitJob(
        self,
        request: "flink_job_pb2.SubmitJobRequest",
        context
    ) -> "flink_job_pb2.SubmitJobResponse":
        """提交 Flink 作业"""
        try:
            submit_request = FlinkJobSubmitRequest(
                template_id=request.template_id,
                job_id=request.job_id,
                job_name=request.job_name,
                job_config=self._struct_to_dict(request.job_config) if request.job_config else {},
                flink_cluster_url=request.flink_cluster_url if request.flink_cluster_url else None,
                savepoint_path=request.savepoint_path if request.savepoint_path else None
            )
            
            job = await self.job_manager.submit_job(submit_request)
            
            # 转换为 proto
            job_pb = flink_job_pb2.FlinkJob(
                job_id=job.job_id,
                job_name=job.job_name,
                template_id=job.template_id,
                flink_job_id=job.flink_job_id or "",
                flink_cluster_url=job.flink_cluster_url,
                status=getattr(flink_job_pb2, job.status.name),
                error_message=job.error_message or "",
                job_config=self._dict_to_struct(job.job_config),
                submitted_by=job.submitted_by or "",
                submitted_at=self._datetime_to_timestamp(datetime.fromisoformat(job.submitted_at)) if job.submitted_at else None,
                start_time=self._datetime_to_timestamp(datetime.fromisoformat(job.start_time)) if job.start_time else None,
                end_time=self._datetime_to_timestamp(datetime.fromisoformat(job.end_time)) if job.end_time else None,
                duration=job.duration or 0,
                num_operators=job.num_operators or 0,
                num_vertices=job.num_vertices or 0
            )
            
            return flink_job_pb2.SubmitJobResponse(
                
                job=job_pb
            )
        
        except Exception as e:
            return flink_job_pb2.SubmitJobResponse(
                job=None
            )
    
    async def GetJob(
        self,
        request: "flink_job_pb2.GetJobRequest",
        context
    ) -> "flink_job_pb2.GetJobResponse":
        """获取作业信息"""
        try:
            job = await self.job_manager.get_job(request.job_id)
            
            if not job:
                return flink_job_pb2.GetJobResponse(
                    job=None
                )
            
            # 转换为 proto
            job_pb = flink_job_pb2.FlinkJob(
                job_id=job.job_id,
                job_name=job.job_name,
                template_id=job.template_id,
                flink_job_id=job.flink_job_id or "",
                flink_cluster_url=job.flink_cluster_url,
                status=getattr(flink_job_pb2, job.status.name),
                error_message=job.error_message or "",
                job_config=self._dict_to_struct(job.job_config),
                submitted_by=job.submitted_by or "",
                submitted_at=self._datetime_to_timestamp(datetime.fromisoformat(job.submitted_at)) if job.submitted_at else None,
                start_time=self._datetime_to_timestamp(datetime.fromisoformat(job.start_time)) if job.start_time else None,
                end_time=self._datetime_to_timestamp(datetime.fromisoformat(job.end_time)) if job.end_time else None,
                duration=job.duration or 0,
                num_operators=job.num_operators or 0,
                num_vertices=job.num_vertices or 0
            )
            
            return flink_job_pb2.GetJobResponse(
                
                job=job_pb
            )
        
        except Exception as e:
            return flink_job_pb2.GetJobResponse(
                job=None
            )
    
    async def ListJobs(
        self,
        request: "flink_job_pb2.ListJobsRequest",
        context
    ) -> "flink_job_pb2.ListJobsResponse":
        """列出所有作业"""
        try:
            jobs = await self.job_manager.list_jobs(status=request.status if request.status else None)
            
            # 转换为 proto
            jobs_pb = []
            for job in jobs:
                job_pb = flink_job_pb2.FlinkJob(
                    job_id=job.job_id,
                    job_name=job.job_name,
                    template_id=job.template_id,
                    flink_job_id=job.flink_job_id or "",
                    flink_cluster_url=job.flink_cluster_url,
                    status=getattr(flink_job_pb2, job.status.name),
                    error_message=job.error_message or "",
                    job_config=self._dict_to_struct(job.job_config),
                    submitted_by=job.submitted_by or "",
                    submitted_at=self._datetime_to_timestamp(datetime.fromisoformat(job.submitted_at)) if job.submitted_at else None,
                    start_time=self._datetime_to_timestamp(datetime.fromisoformat(job.start_time)) if job.start_time else None,
                    end_time=self._datetime_to_timestamp(datetime.fromisoformat(job.end_time)) if job.end_time else None,
                    duration=job.duration or 0,
                    num_operators=job.num_operators or 0,
                    num_vertices=job.num_vertices or 0
                )
                jobs_pb.append(job_pb)
            
            return flink_job_pb2.ListJobsResponse(
                
                jobs=jobs_pb,
                page_info=pagination_pb2.PageInfo(
                    page=request.page,
                    page_size=request.page_size,
                    total=len(jobs),
                    total_pages=(len(jobs) + request.page_size - 1) // request.page_size
                )
            )
        
        except Exception as e:
            return flink_job_pb2.ListJobsResponse(
                jobs=[],
                page_info=pagination_pb2.PageInfo()
            )
    
    async def StopJob(
        self,
        request: "flink_job_pb2.StopJobRequest",
        context
    ) -> "flink_job_pb2.StopJobResponse":
        """停止作业"""
        try:
            result = await self.job_manager.stop_job(request.job_id, force=request.force)
            
            # 获取作业信息
            job = await self.job_manager.get_job(request.job_id)
            
            job_pb = None
            if job:
                job_pb = flink_job_pb2.FlinkJob(
                    job_id=job.job_id,
                    job_name=job.job_name,
                    template_id=job.template_id,
                    flink_job_id=job.flink_job_id or "",
                    flink_cluster_url=job.flink_cluster_url,
                    status=getattr(flink_job_pb2, job.status.name),
                    error_message=job.error_message or "",
                    job_config=self._dict_to_struct(job.job_config),
                    submitted_by=job.submitted_by or "",
                    submitted_at=self._datetime_to_timestamp(datetime.fromisoformat(job.submitted_at)) if job.submitted_at else None,
                    start_time=self._datetime_to_timestamp(datetime.fromisoformat(job.start_time)) if job.start_time else None,
                    end_time=self._datetime_to_timestamp(datetime.fromisoformat(job.end_time)) if job.end_time else None,
                    duration=job.duration or 0,
                    num_operators=job.num_operators or 0,
                    num_vertices=job.num_vertices or 0
                )
            
            return flink_job_pb2.StopJobResponse(
                
                job=job_pb
            )
        
        except Exception as e:
            return flink_job_pb2.StopJobResponse(
                job=None
            )
    
    async def GetClusterInfo(
        self,
        request: "flink_job_pb2.GetClusterInfoRequest",
        context
    ) -> "flink_job_pb2.GetClusterInfoResponse":
        """获取 Flink 集群信息"""
        try:
            info = await self.job_manager.get_cluster_info()
            
            return flink_job_pb2.GetClusterInfoResponse(
                
                cluster_info=self._dict_to_struct(info)
            )
        
        except Exception as e:
            return flink_job_pb2.GetClusterInfoResponse(
                cluster_info=None
            )
    
    async def ListClusterJobs(
        self,
        request: "flink_job_pb2.ListClusterJobsRequest",
        context
    ) -> "flink_job_pb2.ListClusterJobsResponse":
        """列出 Flink 集群中的所有作业"""
        try:
            jobs = await self.job_manager.list_flink_jobs()
            
            jobs_pb = []
            for job in jobs:
                jobs_pb.append(self._dict_to_struct(job))
            
            return flink_job_pb2.ListClusterJobsResponse(
                
                jobs=jobs_pb
            )
        
        except Exception as e:
            return flink_job_pb2.ListClusterJobsResponse(
                jobs=[]
            )

