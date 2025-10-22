"""
作业管理API
管理Flink作业、Celery任务等的启动、停止、监控
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from app.api.dependencies import get_tenant_user_context
from app.models.base import ResponseModel
from app.services.job_manager import get_job_manager, JobType


router = APIRouter()


class JobStartRequest(BaseModel):
    """启动作业请求"""
    job_id: str


class JobStopRequest(BaseModel):
    """停止作业请求"""
    job_id: str
    force: bool = False


@router.get("/list")
async def list_jobs(
    job_type: Optional[str] = Query(None, description="作业类型过滤"),
    context=Depends(get_tenant_user_context)
):
    """
    列出所有作业
    
    权限: 需要管理员权限
    """
    job_manager = get_job_manager()
    
    # 过滤作业类型
    filter_type = None
    if job_type:
        try:
            filter_type = JobType(job_type)
        except ValueError:
            pass
    
    jobs = job_manager.list_jobs(filter_type)
    
    return ResponseModel(
        message="查询成功",
        data={
            "jobs": jobs,
            "total": len(jobs)
        }
    )


@router.get("/{job_id}")
async def get_job_status(
    job_id: str,
    context=Depends(get_tenant_user_context)
):
    """获取作业状态"""
    job_manager = get_job_manager()
    
    status = job_manager.get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="作业不存在")
    
    return ResponseModel(
        message="查询成功",
        data=status
    )


@router.post("/start")
async def start_job(
    request: JobStartRequest,
    context=Depends(get_tenant_user_context)
):
    """启动作业"""
    job_manager = get_job_manager()
    
    result = await job_manager.start_job(request.job_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return ResponseModel(
        message=result["message"],
        data=result.get("job")
    )


@router.post("/stop")
async def stop_job(
    request: JobStopRequest,
    context=Depends(get_tenant_user_context)
):
    """停止作业"""
    job_manager = get_job_manager()
    
    result = await job_manager.stop_job(request.job_id, request.force)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return ResponseModel(
        message=result["message"],
        data=result.get("job")
    )


@router.post("/restart/{job_id}")
async def restart_job(
    job_id: str,
    context=Depends(get_tenant_user_context)
):
    """重启作业"""
    job_manager = get_job_manager()
    
    result = await job_manager.restart_job(job_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return ResponseModel(
        message=result["message"],
        data=result.get("job")
    )


@router.post("/batch/start")
async def batch_start_jobs(
    job_ids: List[str],
    context=Depends(get_tenant_user_context)
):
    """批量启动作业"""
    job_manager = get_job_manager()
    
    results = []
    for job_id in job_ids:
        result = await job_manager.start_job(job_id)
        results.append({
            "job_id": job_id,
            "success": result["success"],
            "message": result["message"]
        })
    
    return ResponseModel(
        message=f"批量操作完成",
        data={"results": results}
    )


@router.post("/batch/stop")
async def batch_stop_jobs(
    job_ids: List[str],
    force: bool = False,
    context=Depends(get_tenant_user_context)
):
    """批量停止作业"""
    job_manager = get_job_manager()
    
    results = []
    for job_id in job_ids:
        result = await job_manager.stop_job(job_id, force)
        results.append({
            "job_id": job_id,
            "success": result["success"],
            "message": result["message"]
        })
    
    return ResponseModel(
        message=f"批量操作完成",
        data={"results": results}
    )


@router.get("/types")
async def get_job_types():
    """获取作业类型列表"""
    return ResponseModel(
        message="查询成功",
        data={
            "types": [
                {"value": "flink", "label": "Flink实时作业"},
                {"value": "celery", "label": "Celery异步任务"},
                {"value": "model_training", "label": "模型训练"},
                {"value": "data_sync", "label": "数据同步"}
            ]
        }
    )

