"""
Flink 作业管理服务
通过 Flink REST API 管理作业的启动、停止、暂停、恢复等操作
"""
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urljoin
import logging

from app.core.config import settings
from app.models.flink_job_template import (
    JobTemplate, FlinkJob, JobStatus, JobTemplateType,
    JobTemplateCreate, FlinkJobSubmitRequest
)
from app.core.database import mongodb

logger = logging.getLogger(__name__)


class FlinkJobManager:
    """
    Flink 作业管理器
    
    功能：
    1. 通过 REST API 提交作业到 Flink 集群
    2. 停止、暂停、恢复作业
    3. 查询作业状态
    4. 管理作业模板（存储在 MongoDB）
    """
    
    def __init__(self, flink_rest_url: Optional[str] = None):
        """
        初始化 Flink 作业管理器
        
        Args:
            flink_rest_url: Flink REST API 地址（默认从配置读取）
        """
        self.flink_rest_url = flink_rest_url or settings.flink_rest_url
        self.timeout = settings.flink_rest_timeout
        
        # HTTP 客户端
        self.client = httpx.AsyncClient(
            base_url=self.flink_rest_url,
            timeout=self.timeout
        )
        
        logger.info(f"初始化 FlinkJobManager: {self.flink_rest_url}")
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
    
    # ========== Flink 集群操作（通过 REST API） ==========
    
    async def get_cluster_info(self) -> Dict[str, Any]:
        """获取 Flink 集群信息"""
        try:
            response = await self.client.get("/overview")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取集群信息失败: {e}")
            raise
    
    async def list_flink_jobs(self) -> List[Dict[str, Any]]:
        """
        列出 Flink 集群中的所有作业
        
        Returns:
            作业列表
        """
        try:
            response = await self.client.get("/jobs")
            response.raise_for_status()
            data = response.json()
            return data.get("jobs", [])
        except Exception as e:
            logger.error(f"列出作业失败: {e}")
            raise
    
    async def get_flink_job_status(self, flink_job_id: str) -> Dict[str, Any]:
        """
        获取 Flink 作业状态
        
        Args:
            flink_job_id: Flink Job ID
            
        Returns:
            作业状态信息
        """
        try:
            response = await self.client.get(f"/jobs/{flink_job_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取作业状态失败: {e}")
            raise
    
    async def stop_flink_job(self, flink_job_id: str, savepoint: bool = False) -> Dict[str, Any]:
        """
        停止 Flink 作业
        
        Args:
            flink_job_id: Flink Job ID
            savepoint: 是否创建 Savepoint
            
        Returns:
            操作结果
        """
        try:
            url = f"/jobs/{flink_job_id}/stop"
            if savepoint:
                url = f"/jobs/{flink_job_id}/stop?drain=false"  # 可以设置 drain 参数
            
            response = await self.client.post(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"停止作业失败: {e}")
            raise
    
    async def cancel_flink_job(self, flink_job_id: str) -> Dict[str, Any]:
        """
        取消 Flink 作业（立即停止）
        
        Args:
            flink_job_id: Flink Job ID
            
        Returns:
            操作结果
        """
        try:
            response = await self.client.post(f"/jobs/{flink_job_id}/cancel")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"取消作业失败: {e}")
            raise
    
    async def suspend_flink_job(self, flink_job_id: str) -> Dict[str, Any]:
        """
        暂停 Flink 作业（创建 Savepoint 并停止）
        
        Args:
            flink_job_id: Flink Job ID
            
        Returns:
            操作结果（包含 Savepoint 路径）
        """
        try:
            response = await self.client.post(f"/jobs/{flink_job_id}/stop")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"暂停作业失败: {e}")
            raise
    
    # ========== 作业模板管理（存储在 MongoDB） ==========
    
    async def create_job_template(self, template_data: JobTemplateCreate) -> JobTemplate:
        """
        创建作业模板
        
        Args:
            template_data: 模板数据
            
        Returns:
            创建的模板
        """
        db = mongodb.get_database()
        collection = db.job_templates
        
        # 检查是否已存在
        existing = await collection.find_one({"template_id": template_data.template_id})
        if existing:
            raise ValueError(f"模板已存在: {template_data.template_id}")
        
        # 创建模板
        template = JobTemplate(
            **template_data.dict(),
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await collection.insert_one(template.dict())
        logger.info(f"创建作业模板: {template_data.template_id}")
        
        return template
    
    async def get_job_template(self, template_id: str) -> Optional[JobTemplate]:
        """获取作业模板"""
        db = mongodb.get_database()
        collection = db.job_templates
        
        template_doc = await collection.find_one({"template_id": template_id})
        if not template_doc:
            return None
        
        return JobTemplate(**template_doc)
    
    async def list_job_templates(self, status: Optional[str] = "active") -> List[JobTemplate]:
        """列出作业模板"""
        db = mongodb.get_database()
        collection = db.job_templates
        
        query = {}
        if status:
            query["status"] = status
        
        templates = []
        async for doc in collection.find(query):
            templates.append(JobTemplate(**doc))
        
        return templates
    
    # ========== 作业实例管理（存储在 MongoDB） ==========
    
    async def submit_job(
        self,
        request: FlinkJobSubmitRequest,
        submitted_by: Optional[str] = None
    ) -> FlinkJob:
        """
        提交 Flink 作业
        
        Args:
            request: 提交请求
            submitted_by: 提交者
            
        Returns:
            作业实例
        """
        # 1. 获取模板
        template = await self.get_job_template(request.template_id)
        if not template:
            raise ValueError(f"模板不存在: {request.template_id}")
        
        if template.status != "active":
            raise ValueError(f"模板不可用: {request.template_id} (status: {template.status})")
        
        # 2. 根据模板类型提交作业
        if template.job_type == JobTemplateType.PYTHON_SCRIPT:
            flink_job_id = await self._submit_python_script(template, request)
        elif template.job_type == JobTemplateType.JAR:
            flink_job_id = await self._submit_jar(template, request)
        elif template.job_type == JobTemplateType.SQL:
            flink_job_id = await self._submit_sql(template, request)
        elif template.job_type == JobTemplateType.PYTHON_FLINK:
            flink_job_id = await self._submit_python_flink(template, request)
        else:
            raise ValueError(f"不支持的作业类型: {template.job_type}")
        
        # 3. 保存作业实例到 MongoDB
        flink_job = FlinkJob(
            job_id=request.job_id,
            job_name=request.job_name,
            template_id=request.template_id,
            flink_job_id=flink_job_id,
            flink_cluster_url=request.flink_cluster_url or self.flink_rest_url,
            status=JobStatus.RUNNING,
            job_config={
                **template.config,
                **request.job_config
            },
            submitted_by=submitted_by,
            submitted_at=datetime.utcnow().isoformat(),
            start_time=datetime.utcnow().isoformat()
        )
        
        db = mongodb.get_database()
        collection = db.flink_jobs
        await collection.insert_one(flink_job.dict())
        
        logger.info(f"提交 Flink 作业: {request.job_id} (Flink Job ID: {flink_job_id})")
        
        return flink_job
    
    async def _submit_python_script(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest
    ) -> str:
        """
        提交 Python 脚本作业
        
        注意：Flink 不支持直接提交 Python 脚本，需要：
        1. 打包成 JAR（使用 pyflink-submit）
        2. 或者使用 PyFlink Table API（SQL）
        
        这里先实现一个简化版本，实际应该使用 pyflink-submit
        """
        # TODO: 实现 Python 脚本提交逻辑
        # 可以使用 pyflink-submit 或打包成 JAR
        raise NotImplementedError("Python 脚本提交功能待实现（需要 pyflink-submit 或打包成 JAR）")
    
    async def _submit_jar(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest
    ) -> str:
        """
        提交 JAR 作业
        
        Args:
            template: 作业模板
            request: 提交请求
            
        Returns:
            Flink Job ID
        """
        # 1. 上传 JAR（如果还未上传）
        jar_path = template.config.get("jar_path")
        if not jar_path:
            raise ValueError("JAR 路径未配置")
        
        # 2. 提交作业
        # POST /jars/{jar-id}/run
        jar_id = await self._upload_jar_if_needed(jar_path)
        
        # 3. 构建运行参数
        entry_class = template.config.get("main_class")
        if not entry_class:
            raise ValueError("主类未配置")
        
        program_args = request.job_config.get("args", [])
        
        # 提交作业
        response = await self.client.post(
            f"/jars/{jar_id}/run",
            json={
                "entryClass": entry_class,
                "programArgs": " ".join(program_args) if program_args else "",
                "parallelism": request.job_config.get("parallelism", template.parallelism),
                "savepointPath": request.savepoint_path
            }
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get("jobid")
    
    async def _submit_sql(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest
    ) -> str:
        """提交 SQL 作业"""
        # TODO: 实现 SQL 提交逻辑
        raise NotImplementedError("SQL 提交功能待实现")
    
    async def _submit_python_flink(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest
    ) -> str:
        """提交 PyFlink 作业"""
        # TODO: 实现 PyFlink 提交逻辑
        raise NotImplementedError("PyFlink 提交功能待实现")
    
    async def _upload_jar_if_needed(self, jar_path: str) -> str:
        """
        上传 JAR 文件到 Flink 集群（如果需要）
        
        Args:
            jar_path: JAR 文件路径
            
        Returns:
            JAR ID
        """
        # TODO: 实现 JAR 上传逻辑
        # 检查 JAR 是否已上传，如果没有则上传
        raise NotImplementedError("JAR 上传功能待实现")
    
    async def stop_job(self, job_id: str, force: bool = False) -> Dict[str, Any]:
        """
        停止作业
        
        Args:
            job_id: 作业ID（本地）
            force: 是否强制停止
            
        Returns:
            操作结果
        """
        # 1. 从 MongoDB 获取作业信息
        db = mongodb.get_database()
        collection = db.flink_jobs
        
        job_doc = await collection.find_one({"job_id": job_id})
        if not job_doc:
            raise ValueError(f"作业不存在: {job_id}")
        
        flink_job = FlinkJob(**job_doc)
        
        if not flink_job.flink_job_id:
            raise ValueError(f"作业未提交到 Flink 集群: {job_id}")
        
        # 2. 停止 Flink 作业
        if force:
            result = await self.cancel_flink_job(flink_job.flink_job_id)
        else:
            result = await self.stop_flink_job(flink_job.flink_job_id)
        
        # 3. 更新作业状态
        await collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": JobStatus.CANCELLED if force else JobStatus.FINISHED,
                    "end_time": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result
    
    async def get_job(self, job_id: str) -> Optional[FlinkJob]:
        """获取作业信息"""
        db = mongodb.get_database()
        collection = db.flink_jobs
        
        job_doc = await collection.find_one({"job_id": job_id})
        if not job_doc:
            return None
        
        # 如果作业在运行，从 Flink 集群同步状态
        flink_job = FlinkJob(**job_doc)
        if flink_job.flink_job_id and flink_job.status == JobStatus.RUNNING:
            try:
                flink_status = await self.get_flink_job_status(flink_job.flink_job_id)
                flink_state = flink_status.get("state", "").lower()
                
                # 更新状态
                job_status_map = {
                    "running": JobStatus.RUNNING,
                    "finished": JobStatus.FINISHED,
                    "failed": JobStatus.FAILED,
                    "cancelled": JobStatus.CANCELLED,
                    "suspended": JobStatus.SUSPENDED
                }
                
                new_status = job_status_map.get(flink_state, JobStatus.RUNNING)
                
                if new_status != flink_job.status:
                    await collection.update_one(
                        {"job_id": job_id},
                        {
                            "$set": {
                                "status": new_status,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    flink_job.status = new_status
            except Exception as e:
                logger.warning(f"同步作业状态失败: {e}")
        
        return flink_job
    
    async def list_jobs(self, status: Optional[str] = None) -> List[FlinkJob]:
        """列出所有作业"""
        db = mongodb.get_database()
        collection = db.flink_jobs
        
        query = {}
        if status:
            query["status"] = status
        
        jobs = []
        async for doc in collection.find(query).sort("submitted_at", -1):
            jobs.append(FlinkJob(**doc))
        
        return jobs


# 全局单例
_flink_job_manager: Optional[FlinkJobManager] = None


def get_flink_job_manager(flink_rest_url: Optional[str] = None) -> FlinkJobManager:
    """获取 Flink 作业管理器单例"""
    global _flink_job_manager
    if _flink_job_manager is None:
        _flink_job_manager = FlinkJobManager(flink_rest_url)
    return _flink_job_manager

