"""Flink 作业管理相关的 Celery 任务"""
import asyncio
from typing import List
from app.tasks.celery_app import celery_app
from app.core.database import mongodb
from app.services.flink.job_manager import get_flink_job_manager
from app.models.flink_job_template import JobStatus
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="sync_flink_job_status")
def sync_flink_job_status():
    """
    定期同步 Flink 作业状态
    
    - 对于 Python 作业：从 K8s Job 日志提取 Flink Job ID
    - 对于所有作业：从 Flink REST API 查询最新状态
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_sync_all_jobs())
        logger.info(f"作业状态同步完成: 成功 {result['success']} 个, 失败 {result['failed']} 个")
        return result
    finally:
        loop.close()


async def _sync_all_jobs():
    """同步所有需要更新的作业"""
    await mongodb.connect()
    db = mongodb.get_database()
    collection = db.flink_jobs
    
    job_manager = get_flink_job_manager()
    
    # 查询所有非最终状态的作业
    query = {
        "status": {
            "$in": [
                JobStatus.CREATED.value,
                JobStatus.RUNNING.value,
                JobStatus.SUSPENDED.value
            ]
        }
    }
    
    success_count = 0
    failed_count = 0
    
    async for doc in collection.find(query):
        job_id = doc.get("job_id")
        try:
            # 同步状态
            result = await job_manager.sync_job_status_from_k8s(job_id)
            if result:
                success_count += 1
            else:
                failed_count += 1
        except Exception as e:
            logger.error(f"同步作业状态失败: {job_id}, 错误: {e}")
            failed_count += 1
    
    return {
        "success": success_count,
        "failed": failed_count
    }


@celery_app.task(name="cleanup_completed_k8s_jobs")
def cleanup_completed_k8s_jobs():
    """
    清理已完成的 Kubernetes Job
    
    - 清理超过 24 小时的已完成/失败的 K8s Job
    - 保留日志用于问题排查
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_cleanup_jobs())
        logger.info(f"K8s Job 清理完成: 删除 {result['deleted']} 个")
        return result
    finally:
        loop.close()


async def _cleanup_jobs():
    """清理 K8s Job"""
    from kubernetes import client as k8s_client, config as k8s_config
    from datetime import datetime, timedelta
    
    try:
        # 加载 K8s 配置
        try:
            k8s_config.load_incluster_config()
        except Exception:
            k8s_config.load_kube_config()
        
        batch_v1 = k8s_client.BatchV1Api()
        namespace = "lemo-dev"
        
        # 查询所有 Flink Python Job
        jobs = batch_v1.list_namespaced_job(
            namespace=namespace,
            label_selector="app=flink-python-job"
        )
        
        deleted_count = 0
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        for job in jobs.items:
            # 检查 Job 是否完成且超过保留时间
            completion_time = job.status.completion_time
            if completion_time and completion_time < cutoff_time:
                try:
                    # 删除 Job（会自动清理关联的 Pod）
                    batch_v1.delete_namespaced_job(
                        name=job.metadata.name,
                        namespace=namespace,
                        propagation_policy='Background'
                    )
                    logger.info(f"删除 K8s Job: {job.metadata.name}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"删除 K8s Job 失败: {job.metadata.name}, 错误: {e}")
        
        return {"deleted": deleted_count}
        
    except Exception as e:
        logger.error(f"清理 K8s Job 失败: {e}")
        return {"deleted": 0}


