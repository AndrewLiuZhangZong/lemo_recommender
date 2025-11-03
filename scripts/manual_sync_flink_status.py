#!/usr/bin/env python3
"""
手动触发 Flink 作业状态同步
用于测试和调试
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import mongodb
from app.services.flink.job_manager import get_flink_job_manager
from app.models.flink_job_template import JobStatus
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def sync_all_jobs():
    """同步所有需要更新的作业"""
    try:
        # 连接数据库
        await mongodb.connect()
        db = mongodb.get_database()
        collection = db.flink_jobs
        
        # 获取 Job Manager
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
        
        logger.info("=" * 60)
        logger.info("开始同步 Flink 作业状态")
        logger.info("=" * 60)
        
        # 统计
        total_count = await collection.count_documents(query)
        logger.info(f"找到 {total_count} 个待同步的作业")
        
        if total_count == 0:
            logger.info("没有需要同步的作业")
            return
        
        success_count = 0
        failed_count = 0
        
        # 同步每个作业
        async for doc in collection.find(query):
            job_id = doc.get("job_id")
            current_status = doc.get("status")
            flink_job_id = doc.get("flink_job_id")
            
            logger.info("-" * 60)
            logger.info(f"同步作业: {job_id}")
            logger.info(f"  当前状态: {current_status}")
            logger.info(f"  Flink Job ID: {flink_job_id or '(未提取)'}")
            
            try:
                # 同步状态
                result = await job_manager.sync_job_status_from_k8s(job_id)
                if result:
                    success_count += 1
                    logger.info(f"  ✓ 同步成功")
                    
                    # 读取更新后的状态
                    updated_doc = await collection.find_one({"job_id": job_id})
                    if updated_doc:
                        new_status = updated_doc.get("status")
                        new_flink_job_id = updated_doc.get("flink_job_id")
                        logger.info(f"  更新后状态: {new_status}")
                        if new_flink_job_id and new_flink_job_id != flink_job_id:
                            logger.info(f"  提取到 Flink Job ID: {new_flink_job_id}")
                else:
                    failed_count += 1
                    logger.warning(f"  × 同步失败或无需更新")
            except Exception as e:
                logger.error(f"  × 同步出错: {e}", exc_info=True)
                failed_count += 1
        
        # 总结
        logger.info("=" * 60)
        logger.info(f"同步完成: 成功 {success_count} 个, 失败 {failed_count} 个")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"同步过程出错: {e}", exc_info=True)
    finally:
        # 关闭数据库连接
        await mongodb.close()


async def sync_single_job(job_id: str):
    """同步单个作业"""
    try:
        # 连接数据库
        await mongodb.connect()
        db = mongodb.get_database()
        collection = db.flink_jobs
        
        # 查询作业
        doc = await collection.find_one({"job_id": job_id})
        if not doc:
            logger.error(f"作业不存在: {job_id}")
            return
        
        logger.info("=" * 60)
        logger.info(f"同步作业: {job_id}")
        logger.info(f"  当前状态: {doc.get('status')}")
        logger.info(f"  Flink Job ID: {doc.get('flink_job_id') or '(未提取)'}")
        logger.info("=" * 60)
        
        # 获取 Job Manager
        job_manager = get_flink_job_manager()
        
        # 同步状态
        result = await job_manager.sync_job_status_from_k8s(job_id)
        
        if result:
            logger.info("✓ 同步成功")
            
            # 读取更新后的状态
            updated_doc = await collection.find_one({"job_id": job_id})
            if updated_doc:
                logger.info(f"更新后状态: {updated_doc.get('status')}")
                if updated_doc.get('flink_job_id'):
                    logger.info(f"Flink Job ID: {updated_doc.get('flink_job_id')}")
        else:
            logger.warning("× 同步失败或无需更新")
            
    except Exception as e:
        logger.error(f"同步出错: {e}", exc_info=True)
    finally:
        await mongodb.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 同步指定的作业
        job_id = sys.argv[1]
        asyncio.run(sync_single_job(job_id))
    else:
        # 同步所有作业
        asyncio.run(sync_all_jobs())

