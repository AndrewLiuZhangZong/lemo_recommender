"""
Flink 作业管理服务
通过 Flink REST API 管理作业的启动、停止、暂停、恢复等操作
"""
import httpx
import asyncio
import os
import tempfile
import aiohttp
import aiofiles
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
        try:
            db = mongodb.get_database()
            if db is None:
                raise RuntimeError("MongoDB 数据库连接未建立")
            
            collection = db.job_templates
            logger.info(f"准备创建作业模板: template_id={template_data.template_id}, name={template_data.name}")
            
            # 检查是否已存在
            existing = await collection.find_one({"template_id": template_data.template_id})
            if existing:
                logger.warning(f"模板已存在: {template_data.template_id}")
                raise ValueError(f"模板已存在: {template_data.template_id}")
            
            # 创建模板
            template = JobTemplate(
                **template_data.dict(),
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # 转换为字典并插入
            template_dict = template.dict()
            logger.info(f"准备插入模板数据到 MongoDB: {template_dict}")
            
            result = await collection.insert_one(template_dict)
            logger.info(f"MongoDB 插入结果: inserted_id={result.inserted_id}, template_id={template_data.template_id}")
            
            # 验证是否插入成功
            if not result.inserted_id:
                raise RuntimeError("MongoDB 插入操作失败，未返回 inserted_id")
            
            # 验证数据是否真的存在
            verify = await collection.find_one({"template_id": template_data.template_id})
            if not verify:
                raise RuntimeError(f"模板插入后验证失败: template_id={template_data.template_id}")
            
            logger.info(f"✓ 作业模板创建成功: template_id={template_data.template_id}, name={template_data.name}")
            return template
            
        except ValueError:
            # 参数错误，直接抛出
            raise
        except Exception as e:
            logger.error(f"创建作业模板失败: {e}", exc_info=True)
            raise RuntimeError(f"创建作业模板失败: {str(e)}") from e
    
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
        
        # 2. 生成 job_id（如果没有指定）
        job_id = request.job_id
        if not job_id:
            # 生成格式：template_id_timestamp
            import time
            job_id = f"{request.template_id}_{int(time.time()*1000)}"
            logger.info(f"自动生成 job_id: {job_id}")
        
        # 3. 先创建作业实例记录（即使提交失败也保存记录）
        flink_job = FlinkJob(
            job_id=job_id,
            job_name=request.job_name,
            template_id=request.template_id,
            flink_job_id=None,  # 初始为空，提交成功后再更新
            flink_cluster_url=request.flink_cluster_url or self.flink_rest_url,
            status=JobStatus.CREATED,  # 初始状态为 CREATED
            job_config={
                **template.config,
                **request.job_config
            },
            submitted_by=submitted_by,
            submitted_at=datetime.utcnow().isoformat(),
            start_time=None  # 提交成功后再设置
        )
        
        db = mongodb.get_database()
        if db is None:
            raise RuntimeError("MongoDB 数据库连接未建立")
        
        collection = db.flink_jobs
        await collection.insert_one(flink_job.dict())
        logger.info(f"创建作业实例记录: {job_id}")
        
        # 4. 尝试提交到 Flink 集群
        flink_job_id = None
        error_message = None
        try:
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
            
            # 提交成功，更新作业状态
            flink_job.flink_job_id = flink_job_id
            flink_job.status = JobStatus.RUNNING
            flink_job.start_time = datetime.utcnow().isoformat()
            flink_job.error_message = None
            
            await collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "flink_job_id": flink_job_id,
                        "status": JobStatus.RUNNING.value,
                        "start_time": flink_job.start_time,
                        "error_message": None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"✓ Flink 作业提交成功: {job_id} (Flink Job ID: {flink_job_id})")
            
        except NotImplementedError as e:
            # 作业类型暂未实现，更新状态为失败
            error_message = str(e)
            flink_job.status = JobStatus.FAILED
            flink_job.error_message = error_message
            
            await collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "status": JobStatus.FAILED.value,
                        "error_message": error_message,
                        "end_time": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.warning(f"⚠️ Flink 作业提交失败（功能未实现）: {job_id}, 错误: {error_message}")
            
        except Exception as e:
            # 其他错误，更新状态为失败
            error_message = str(e)
            flink_job.status = JobStatus.FAILED
            flink_job.error_message = error_message
            
            await collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "status": JobStatus.FAILED.value,
                        "error_message": error_message,
                        "end_time": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.error(f"✗ Flink 作业提交失败: {job_id}, 错误: {error_message}", exc_info=True)
            # 抛出异常，让上层处理
            raise
        
        return flink_job
    
    async def _submit_python_script(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest
    ) -> str:
        """
        提交 Python 脚本作业
        
        注意: Flink REST API 的 /jars/upload 只接受 JAR 文件。
        Python 作业通过 Kubernetes Job 使用 `flink run -py` 命令提交。
        
        Args:
            template: 作业模板
            request: 提交请求
            
        Returns:
            Kubernetes Job 名称（作为作业 ID）
        """
        script_path = template.config.get("script_path")
        if not script_path:
            raise ValueError("脚本路径未配置")
        
        entry_point = template.config.get("entry_point", "main")
        args = template.config.get("args", [])
        
        # 合并运行时参数
        if "args" in request.job_config:
            args = request.job_config["args"]
        
        parallelism = int(request.job_config.get("parallelism", template.parallelism or 1))
        
        logger.info(f"准备通过 Kubernetes Job 提交 Python 脚本作业: {script_path}")
        
        # 从配置读取 JobManager RPC 地址
        from app.core.config import settings
        jobmanager_rpc_address = settings.flink_jobmanager_rpc_address
        
        logger.info(f"JobManager RPC 地址: {jobmanager_rpc_address}, 并行度: {parallelism}")
        
        # 如果是远程脚本（URL），需要在容器中下载
        is_remote = script_path.startswith("http://") or script_path.startswith("https://")
        
        # 获取依赖的 JAR 文件（从模板配置中读取）
        jar_files = template.config.get("jar_files", [])
        
        # 构建基础 flink run 命令
        base_cmd = f"/opt/flink/bin/flink run -m {jobmanager_rpc_address} -p {parallelism}"
        
        # 添加 JAR 依赖
        if jar_files:
            jar_args = " ".join([f"--jarfile {jar}" for jar in jar_files])
            base_cmd += f" {jar_args}"
            logger.info(f"添加 JAR 依赖: {jar_files}")
        
        if is_remote:
            # 构建下载并执行的命令
            script_filename = script_path.split("/")[-1]
            flink_command_str = f"""
set -e
echo "下载 Python 脚本: {script_path}"
wget -O /tmp/{script_filename} {script_path}
echo "脚本下载完成"
echo "开始提交 Flink 作业..."
{base_cmd} -py /tmp/{script_filename}
"""
        else:
            # 本地文件路径
            flink_command_str = f"{base_cmd} -py {script_path}"
        
        # 添加入口点（如果指定）
        if entry_point and entry_point != "main":
            flink_command_str += f" -pym {entry_point}"
        
        # 添加用户参数
        if args:
            flink_command_str += " " + " ".join(args)
        
        logger.info(f"Flink 命令脚本:\n{flink_command_str}")
        
        # 创建 Kubernetes Job
        from kubernetes import client as k8s_client, config as k8s_config
        
        try:
            # 加载 K8s 配置
            k8s_config.load_incluster_config()
        except Exception:
            # 如果不在集群内，尝试加载本地配置
            try:
                k8s_config.load_kube_config()
            except Exception as e:
                raise RuntimeError(f"无法加载 Kubernetes 配置: {e}")
        
        batch_v1 = k8s_client.BatchV1Api()
        
        # 生成唯一的 Job 名称（符合 K8s RFC 1123 规范）
        # 1. 替换下划线为连字符
        # 2. 转换为小写
        # 3. 移除开头/结尾的非字母数字字符
        # 4. 限制长度为 63 字符
        import re
        safe_job_id = request.job_id.replace('_', '-').lower()
        safe_job_id = re.sub(r'^[^a-z0-9]+|[^a-z0-9]+$', '', safe_job_id)  # 移除开头/结尾的非字母数字
        safe_job_id = re.sub(r'[^a-z0-9-]+', '-', safe_job_id)  # 替换其他非法字符为连字符
        job_name = f"flink-py-{safe_job_id}"[:63]
        
        # 确保名称以字母数字结尾（防止截断后以 '-' 结尾）
        job_name = re.sub(r'-+$', '', job_name)
        if not job_name or job_name == 'flink-py':
            # 如果处理后名称无效，使用时间戳
            import time
            job_name = f"flink-py-{int(time.time())}"
        
        logger.info(f"生成 K8s Job 名称: {job_name} (原始 job_id: {request.job_id})")
        
        # 构建 Job 配置
        job = k8s_client.V1Job(
            metadata=k8s_client.V1ObjectMeta(
                name=job_name,
                labels={
                    "app": "flink-python-job",
                    "job-id": safe_job_id,  # label 也需要符合规范
                }
            ),
            spec=k8s_client.V1JobSpec(
                template=k8s_client.V1PodTemplateSpec(
                    metadata=k8s_client.V1ObjectMeta(
                        labels={
                            "app": "flink-python-job",
                            "job-id": safe_job_id,  # label 也需要符合规范
                        }
                    ),
                    spec=k8s_client.V1PodSpec(
                        restart_policy="Never",
                        service_account_name="lemo-service-recommender-sa",  # 使用现有 ServiceAccount
                        image_pull_secrets=[k8s_client.V1LocalObjectReference(name="regcred")],  # ACR 镜像拉取凭证
                        containers=[
                            k8s_client.V1Container(
                                name="flink-python-submitter",
                                image="registry.cn-beijing.aliyuncs.com/lemo_zls/flink-python:latest",
                                image_pull_policy="IfNotPresent",
                                command=["/bin/bash", "-c"],
                                args=[flink_command_str],  # 使用完整的命令脚本字符串
                                env=[
                                    k8s_client.V1EnvVar(name="FLINK_REST_URL", value=self.flink_rest_url),
                                ],
                            )
                        ],
                    )
                ),
                backoff_limit=1,  # 失败后重试次数
            )
        )
        
        # 提交 Job
        namespace = "lemo-dev"  # TODO: 从配置读取
        try:
            batch_v1.create_namespaced_job(namespace=namespace, body=job)
            logger.info(f"✓ Kubernetes Job 创建成功: {job_name}")
            
            # 返回 K8s Job 名称（作为临时的 job_id）
            # 注意：真正的 Flink Job ID 需要异步获取
            # 后台任务会定期检查 K8s Job 状态并更新 Flink Job ID
            return job_name
        except Exception as e:
            raise RuntimeError(f"创建 Kubernetes Job 失败: {e}")
    
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
        """
        提交 SQL 作业
        
        通过创建临时 PyFlink 脚本来执行 SQL
        
        Args:
            template: 作业模板
            request: 提交请求
            
        Returns:
            Flink Job ID
        """
        sql = template.config.get("sql")
        sql_file = template.config.get("sql_file")
        
        if not sql and not sql_file:
            raise ValueError("SQL 内容或 SQL 文件路径未配置")
        
        # 如果指定了 SQL 文件，读取内容
        if sql_file:
            if sql_file.startswith(('http://', 'https://')):
                # 从 URL 下载 SQL 文件
                logger.info(f"从 URL 下载 SQL 文件: {sql_file}")
                try:
                    download_response = await self.client.get(sql_file)
                    download_response.raise_for_status()
                    sql = download_response.text
                    logger.info(f"✓ SQL 文件下载成功 ({len(sql)} chars)")
                except Exception as e:
                    raise RuntimeError(f"下载 SQL 文件失败: {sql_file}, 错误: {e}")
            else:
                # 本地文件路径
                if not os.path.exists(sql_file):
                    raise FileNotFoundError(f"SQL 文件不存在: {sql_file}")
                
                async with aiofiles.open(sql_file, 'r', encoding='utf-8') as f:
                    sql = await f.read()
        
        if not sql:
            raise ValueError("SQL 内容为空")
        
        # 创建临时 PyFlink 脚本来执行 SQL
        # 生成 PyFlink Table API 脚本
        pyflink_script = f'''
from pyflink.table import EnvironmentSettings, TableEnvironment
import sys

def main():
    # 创建 Table Environment
    env_settings = EnvironmentSettings.in_streaming_mode()
    table_env = TableEnvironment.create(env_settings)
    
    # 设置并行度
    table_env.get_config().set("parallelism.default", "{template.parallelism}")
    
    # 执行 SQL
    sql_statements = """
{sql}
"""
    
    # 分割多个 SQL 语句并执行
    for statement in sql_statements.strip().split(';'):
        statement = statement.strip()
        if statement:
            print(f"Executing SQL: {{statement[:100]}}...")
            try:
                result = table_env.execute_sql(statement)
                print(f"✓ SQL executed successfully")
            except Exception as e:
                print(f"✗ SQL execution failed: {{e}}")
                raise
    
    print("All SQL statements executed successfully")

if __name__ == '__main__':
    main()
'''
        
        # 写入临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(pyflink_script)
            temp_script_path = tmp.name
        
        try:
            # 上传并提交临时脚本
            logger.info(f"创建临时 PyFlink SQL 脚本: {temp_script_path}")
            
            async with aiofiles.open(temp_script_path, 'rb') as f:
                script_content = await f.read()
            
            # 构建 multipart form data（Flink 要求 field 名称为 'jarfile'）
            form = aiohttp.FormData()
            form.add_field('jarfile',
                          script_content,
                          filename='sql_job.py',
                          content_type='application/x-java-archive')
            
            # 使用 aiohttp 上传文件
            async with aiohttp.ClientSession() as session:
                upload_url = f"{self.flink_rest_url}/jars/upload"
                async with session.post(upload_url, data=form) as upload_response:
                    upload_response.raise_for_status()
                    upload_result = await upload_response.json()
            
            filename = upload_result.get("filename")
            if not filename:
                raise RuntimeError("上传 SQL 脚本失败，未返回文件名")
            
            logger.info(f"SQL 脚本上传成功: {filename}")
            
            # 提交作业
            run_response = await self.client.post(
                f"/jars/{filename}/run",
                json={
                    "programArgs": "",
                    "parallelism": request.job_config.get("parallelism", template.parallelism),
                    "savepointPath": request.savepoint_path
                }
            )
            run_response.raise_for_status()
            
            result = run_response.json()
            job_id = result.get("jobid")
            
            if not job_id:
                raise RuntimeError("提交 SQL 作业失败，未返回 Job ID")
            
            logger.info(f"✓ SQL 作业提交成功: {job_id}")
            return job_id
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_script_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
    
    async def _submit_python_flink(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest
    ) -> str:
        """
        提交 PyFlink 作业
        
        PyFlink 作业与 Python 脚本类似，但使用 PyFlink API
        
        Args:
            template: 作业模板
            request: 提交请求
            
        Returns:
            Flink Job ID
        """
        script_path = template.config.get("script_path")
        if not script_path:
            raise ValueError("PyFlink 脚本路径未配置")
        
        python_env = template.config.get("python_env")
        entry_point = template.config.get("entry_point", "main")
        args = template.config.get("args", [])
        
        # 合并运行时参数
        if "args" in request.job_config:
            args = request.job_config["args"]
        
        # 1. 获取脚本内容
        logger.info(f"准备 PyFlink 脚本: {script_path}")
        
        if script_path.startswith(('http://', 'https://')):
            # 从 URL 下载脚本
            logger.info(f"从 URL 下载 PyFlink 脚本: {script_path}")
            try:
                download_response = await self.client.get(script_path)
                download_response.raise_for_status()
                script_content = download_response.content
                # 从 URL 中提取文件名
                script_filename = script_path.split('/')[-1]
                logger.info(f"✓ PyFlink 脚本下载成功: {script_filename} ({len(script_content)} bytes)")
            except Exception as e:
                raise RuntimeError(f"下载 PyFlink 脚本失败: {script_path}, 错误: {e}")
        else:
            # 本地文件路径
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"PyFlink 脚本文件不存在: {script_path}")
            
            logger.info(f"读取本地 PyFlink 脚本: {script_path}")
            async with aiofiles.open(script_path, 'rb') as f:
                script_content = await f.read()
            script_filename = os.path.basename(script_path)
        
        # 2. 上传 PyFlink 脚本到 Flink
        logger.info(f"上传 PyFlink 脚本到 Flink: {script_filename}")
        
        # 构建 multipart form data（Flink 要求 field 名称为 'jarfile'）
        form = aiohttp.FormData()
        form.add_field('jarfile',
                      script_content,
                      filename=script_filename,
                      content_type='application/x-java-archive')
        
        # 使用 aiohttp 上传文件
        async with aiohttp.ClientSession() as session:
            upload_url = f"{self.flink_rest_url}/jars/upload"
            async with session.post(upload_url, data=form) as upload_response:
                upload_response.raise_for_status()
                upload_result = await upload_response.json()
        
        filename = upload_result.get("filename")
        if not filename:
            raise RuntimeError("上传 PyFlink 脚本失败，未返回文件名")
        
        logger.info(f"✓ PyFlink 脚本上传成功: {filename}")
        
        # 2. 构建运行参数
        program_args_list = ["-py", filename]
        
        # 如果指定了 Python 环境
        if python_env:
            program_args_list.extend(["-pyexec", python_env])
        
        # 如果指定了入口点模块
        if entry_point and entry_point != "main":
            program_args_list.extend(["-pym", entry_point])
        
        # 添加用户参数
        if args:
            program_args_list.extend(args)
        
        # 3. 提交 PyFlink 作业
        run_response = await self.client.post(
            f"/jars/{filename}/run",
            json={
                "programArgs": " ".join(program_args_list),
                "parallelism": request.job_config.get("parallelism", template.parallelism),
                "savepointPath": request.savepoint_path
            }
        )
        run_response.raise_for_status()
        
        result = run_response.json()
        job_id = result.get("jobid")
        
        if not job_id:
            raise RuntimeError("提交 PyFlink 作业失败，未返回 Job ID")
        
        logger.info(f"✓ PyFlink 作业提交成功: {job_id}")
        return job_id
    
    async def _upload_jar_if_needed(self, jar_path: str) -> str:
        """
        上传 JAR 文件到 Flink 集群（如果需要）
        
        Args:
            jar_path: JAR 文件路径
            
        Returns:
            JAR ID（文件名）
        """
        # 检查 JAR 文件是本地路径还是 URL
        if jar_path.startswith(('http://', 'https://')):
            # 从 URL 中提取文件名
            jar_filename = jar_path.split('/')[-1]
        else:
            # 本地文件路径
            if not os.path.exists(jar_path):
                raise FileNotFoundError(f"JAR 文件不存在: {jar_path}")
            jar_filename = os.path.basename(jar_path)
        
        # 1. 检查 JAR 是否已上传
        try:
            list_response = await self.client.get("/jars")
            list_response.raise_for_status()
            jars_data = list_response.json()
            
            # 查找已上传的 JAR
            for jar in jars_data.get("files", []):
                if jar.get("name") == jar_filename or jar.get("id") == jar_filename:
                    logger.info(f"JAR 已存在于 Flink 集群: {jar_filename}")
                    return jar.get("id") or jar_filename
        except Exception as e:
            logger.warning(f"检查已上传 JAR 失败: {e}")
        
        # 2. 获取 JAR 内容
        logger.info(f"准备 JAR 文件: {jar_path}")
        
        if jar_path.startswith(('http://', 'https://')):
            # 从 URL 下载 JAR
            logger.info(f"从 URL 下载 JAR: {jar_path}")
            try:
                download_response = await self.client.get(jar_path)
                download_response.raise_for_status()
                jar_content = download_response.content
                logger.info(f"✓ JAR 下载成功: {jar_filename} ({len(jar_content)} bytes)")
            except Exception as e:
                raise RuntimeError(f"下载 JAR 失败: {jar_path}, 错误: {e}")
        else:
            # 本地文件路径
            logger.info(f"读取本地 JAR: {jar_path}")
            async with aiofiles.open(jar_path, 'rb') as f:
                jar_content = await f.read()
        
        # 3. 上传 JAR 到 Flink
        logger.info(f"上传 JAR 到 Flink: {jar_filename}")
        
        # 构建 multipart form data
        form = aiohttp.FormData()
        form.add_field('jarfile',
                      jar_content,
                      filename=jar_filename,
                      content_type='application/java-archive')
        
        # 使用 aiohttp 上传文件
        async with aiohttp.ClientSession() as session:
            upload_url = f"{self.flink_rest_url}/jars/upload"
            async with session.post(upload_url, data=form) as upload_response:
                upload_response.raise_for_status()
                upload_result = await upload_response.json()
        
        # 获取上传的文件名/ID
        filename = upload_result.get("filename")
        if not filename:
            raise RuntimeError("上传 JAR 失败，未返回文件名")
        
        logger.info(f"✓ JAR 上传成功: {filename}")
        return filename
    
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
        result = {"status": "stopped"}
        
        # 2. 停止 Flink 作业（如果已提交）
        if flink_job.flink_job_id:
            logger.info(f"停止 Flink 作业: {flink_job.flink_job_id}")
            try:
                if force:
                    result = await self.cancel_flink_job(flink_job.flink_job_id)
                else:
                    result = await self.stop_flink_job(flink_job.flink_job_id)
            except Exception as e:
                logger.warning(f"停止 Flink 作业失败（可能已经停止）: {e}")
        else:
            logger.info(f"作业尚未提交到 Flink，尝试停止 K8s Job")
            # 尝试停止 K8s Job（对于 Python 作业）
            try:
                from kubernetes import client as k8s_client, config as k8s_config
                
                # 加载 K8s 配置
                try:
                    k8s_config.load_incluster_config()
                except Exception:
                    try:
                        k8s_config.load_kube_config()
                    except Exception:
                        logger.warning("无法加载 Kubernetes 配置，跳过 K8s Job 清理")
                        pass
                
                # 生成 K8s Job 名称
                import re
                safe_job_id = job_id.replace('_', '-').lower()
                safe_job_id = re.sub(r'^[^a-z0-9]+|[^a-z0-9]+$', '', safe_job_id)
                safe_job_id = re.sub(r'[^a-z0-9-]+', '-', safe_job_id)
                k8s_job_name = f"flink-py-{safe_job_id}"[:63]
                k8s_job_name = re.sub(r'-+$', '', k8s_job_name)
                
                # 删除 K8s Job
                batch_v1 = k8s_client.BatchV1Api()
                namespace = "lemo-dev"
                
                try:
                    batch_v1.delete_namespaced_job(
                        name=k8s_job_name,
                        namespace=namespace,
                        propagation_policy='Background'
                    )
                    logger.info(f"K8s Job 已删除: {k8s_job_name}")
                    result["k8s_job_deleted"] = True
                except Exception as e:
                    logger.warning(f"删除 K8s Job 失败: {e}")
            except Exception as e:
                logger.warning(f"停止 K8s Job 失败: {e}")
        
        # 3. 更新作业状态
        await collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": JobStatus.CANCELLED.value if force else JobStatus.FINISHED.value,
                    "end_time": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"作业状态已更新: {job_id} -> {JobStatus.CANCELLED if force else JobStatus.FINISHED}")
        
        return result
    
    async def pause_job(self, job_id: str) -> Dict[str, Any]:
        """
        暂停作业（创建 Savepoint 并停止）
        
        Args:
            job_id: 作业ID（本地）
            
        Returns:
            操作结果（包含 Savepoint 路径）
        """
        #1. 从 MongoDB 获取作业信息
        db = mongodb.get_database()
        collection = db.flink_jobs
        
        job_doc = await collection.find_one({"job_id": job_id})
        if not job_doc:
            raise ValueError(f"作业不存在: {job_id}")
        
        flink_job = FlinkJob(**job_doc)
        
        if not flink_job.flink_job_id:
            raise ValueError(f"作业未提交到 Flink 集群: {job_id}")
        
        # 2. 暂停 Flink 作业（创建 Savepoint）
        logger.info(f"暂停作业: {job_id}, Flink Job ID: {flink_job.flink_job_id}")
        result = await self.suspend_flink_job(flink_job.flink_job_id)
        
        # 3. 更新作业状态
        update_data = {
            "status": JobStatus.SUSPENDED.value,
            "updated_at": datetime.utcnow()
        }
        
        # 保存 Savepoint 路径（如果返回了）
        if result and "savepoint_path" in result:
            update_data["savepoint_path"] = result["savepoint_path"]
            logger.info(f"Savepoint 已创建: {result['savepoint_path']}")
        
        await collection.update_one(
            {"job_id": job_id},
            {"$set": update_data}
        )
        
        logger.info(f"作业暂停成功: {job_id}")
        return result
    
    async def resume_job(self, job_id: str, savepoint_path: Optional[str] = None) -> Dict[str, Any]:
        """
        恢复作业（从 Savepoint 恢复）
        
        Args:
            job_id: 作业ID（本地）
            savepoint_path: Savepoint 路径（可选，如果不指定则使用作业记录中的路径）
            
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
        
        # 2. 确定 Savepoint 路径
        if not savepoint_path:
            savepoint_path = flink_job.savepoint_path
            if not savepoint_path:
                raise ValueError(f"未找到 Savepoint 路径，无法恢复作业: {job_id}")
        
        logger.info(f"恢复作业: {job_id}, Savepoint: {savepoint_path}")
        
        # 3. 重新提交作业（从 Savepoint）
        # 获取作业模板
        template = await self.get_job_template(flink_job.template_id)
        if not template:
            raise ValueError(f"作业模板不存在: {flink_job.template_id}")
        
        # 构建提交请求
        submit_request = FlinkJobSubmitRequest(
            template_id=flink_job.template_id,
            job_id=job_id,
            job_name=flink_job.job_name,
            job_config=flink_job.job_config,
            savepoint_path=savepoint_path
        )
        
        # 提交作业
        result = await self.submit_job(submit_request)
        
        logger.info(f"作业恢复成功: {job_id}")
        return {"status": "resumed", "job_id": job_id}
    
    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        取消作业（立即停止，不创建 Savepoint）
        
        Args:
            job_id: 作业ID（本地）
            
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
        
        # 2. 取消 Flink 作业
        logger.info(f"取消作业: {job_id}, Flink Job ID: {flink_job.flink_job_id}")
        result = await self.cancel_flink_job(flink_job.flink_job_id)
        
        # 3. 更新作业状态
        await collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": JobStatus.CANCELLED.value,
                    "end_time": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"作业取消成功: {job_id}")
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
    
    async def sync_job_status_from_k8s(self, job_id: str) -> bool:
        """
        从 K8s Job 同步 Flink 作业状态
        
        用于 Python 作业：K8s Job 提交后，需要从 K8s Job 日志中提取 Flink Job ID
        然后查询 Flink REST API 获取真实的作业状态
        
        Args:
            job_id: 作业 ID（对应 K8s Job 名称）
            
        Returns:
            是否成功同步
        """
        from kubernetes import client as k8s_client, config as k8s_config
        
        try:
            # 加载 K8s 配置
            try:
                k8s_config.load_incluster_config()
            except Exception:
                try:
                    k8s_config.load_kube_config()
                except Exception as e:
                    logger.warning(f"无法加载 Kubernetes 配置: {e}")
                    return False
            
            batch_v1 = k8s_client.BatchV1Api()
            core_v1 = k8s_client.CoreV1Api()
            namespace = "lemo-dev"
            
            # 查询数据库中的作业记录
            db = mongodb.get_database()
            collection = db.flink_jobs
            job_doc = await collection.find_one({"job_id": job_id})
            
            if not job_doc:
                logger.warning(f"作业记录不存在: {job_id}")
                return False
            
            flink_job = FlinkJob(**job_doc)
            
            # 如果已经有 Flink Job ID，直接查询 Flink 状态
            if flink_job.flink_job_id:
                return await self._sync_from_flink(flink_job)
            
            # 尝试从 K8s Job 获取 Flink Job ID
            # 注意：必须使用与创建 Job 时完全相同的命名规则
            import re
            safe_job_id = job_id.replace('_', '-').lower()
            safe_job_id = re.sub(r'^[^a-z0-9]+|[^a-z0-9]+$', '', safe_job_id)
            safe_job_id = re.sub(r'[^a-z0-9-]+', '-', safe_job_id)
            k8s_job_name = f"flink-py-{safe_job_id}"[:63]
            k8s_job_name = re.sub(r'-+$', '', k8s_job_name)
            
            if not k8s_job_name or k8s_job_name == 'flink-py':
                logger.warning(f"无法生成有效的 K8s Job 名称: {job_id}")
                return False
            
            # 查询 K8s Job
            try:
                k8s_job = batch_v1.read_namespaced_job(name=k8s_job_name, namespace=namespace)
            except Exception as e:
                logger.warning(f"K8s Job 不存在: {k8s_job_name}, 错误: {e}")
                return False
            
            # 检查 Job 状态
            if k8s_job.status.succeeded:
                # Job 成功完成，尝试从日志中提取 Flink Job ID
                pods = core_v1.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=f"job-name={k8s_job_name}"
                )
                
                if pods.items:
                    pod = pods.items[0]
                    try:
                        logs = core_v1.read_namespaced_pod_log(
                            name=pod.metadata.name,
                            namespace=namespace
                        )
                        
                        # 从日志中提取 Flink Job ID（格式: Job has been submitted with JobID xxx）
                        import re
                        match = re.search(r'Job has been submitted with JobID ([a-f0-9]+)', logs)
                        if match:
                            flink_job_id = match.group(1)
                            logger.info(f"从 K8s Job 日志中提取到 Flink Job ID: {flink_job_id}")
                            
                            # 更新数据库
                            flink_job.flink_job_id = flink_job_id
                            flink_job.status = JobStatus.RUNNING
                            await collection.update_one(
                                {"job_id": job_id},
                                {"$set": {
                                    "flink_job_id": flink_job_id,
                                    "status": JobStatus.RUNNING.value
                                }}
                            )
                            
                            # 继续同步 Flink 状态
                            return await self._sync_from_flink(flink_job)
                    except Exception as e:
                        logger.warning(f"读取 Pod 日志失败: {e}")
            
            elif k8s_job.status.failed:
                # Job 失败
                logger.warning(f"K8s Job 执行失败: {k8s_job_name}")
                await collection.update_one(
                    {"job_id": job_id},
                    {"$set": {
                        "status": JobStatus.FAILED.value,
                        "error_message": "Kubernetes Job 执行失败"
                    }}
                )
                return True
            
            # Job 还在运行中，暂不更新
            return False
            
        except Exception as e:
            logger.error(f"同步作业状态失败: {job_id}, 错误: {e}", exc_info=True)
            return False
    
    async def _sync_from_flink(self, job: FlinkJob) -> bool:
        """从 Flink REST API 同步作业状态"""
        try:
            if not job.flink_job_id:
                return False
            
            # 查询 Flink 作业状态
            response = await self.client.get(f"/jobs/{job.flink_job_id}")
            response.raise_for_status()
            
            flink_status = response.json()
            state = flink_status.get("state", "").upper()
            
            # 映射 Flink 状态到我们的状态
            status_mapping = {
                "CREATED": JobStatus.CREATED,
                "RUNNING": JobStatus.RUNNING,
                "FINISHED": JobStatus.FINISHED,
                "FAILED": JobStatus.FAILED,
                "CANCELED": JobStatus.CANCELLED,
                "CANCELLING": JobStatus.RUNNING,
                "RESTARTING": JobStatus.RUNNING,
                "SUSPENDED": JobStatus.SUSPENDED,
            }
            
            new_status = status_mapping.get(state, JobStatus.RUNNING)
            
            # 更新数据库
            db = mongodb.get_database()
            collection = db.flink_jobs
            
            update_data = {
                "status": new_status.value,
            }
            
            # 如果作业完成，记录结束时间
            if new_status in [JobStatus.FINISHED, JobStatus.FAILED, JobStatus.CANCELLED]:
                update_data["end_time"] = datetime.utcnow().isoformat()
                
                # 计算运行时长
                if job.start_time:
                    start = datetime.fromisoformat(job.start_time)
                    end = datetime.utcnow()
                    update_data["duration"] = int((end - start).total_seconds())
            
            await collection.update_one(
                {"job_id": job.job_id},
                {"$set": update_data}
            )
            
            logger.info(f"同步作业状态成功: {job.job_id}, Flink 状态: {state} -> {new_status.value}")
            return True
            
        except Exception as e:
            logger.error(f"从 Flink 同步状态失败: {job.job_id}, 错误: {e}")
            return False


# 全局单例
_flink_job_manager: Optional[FlinkJobManager] = None


def get_flink_job_manager(flink_rest_url: Optional[str] = None) -> FlinkJobManager:
    """获取 Flink 作业管理器单例"""
    global _flink_job_manager
    if _flink_job_manager is None:
        _flink_job_manager = FlinkJobManager(flink_rest_url)
    return _flink_job_manager