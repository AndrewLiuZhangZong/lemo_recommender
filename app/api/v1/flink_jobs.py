"""
Flink 作业管理 API
支持通过 REST API 管理 Flink 作业的启动、停止、暂停、恢复等操作
支持动态注册作业模板，不限于固定的3种作业类型
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from app.api.dependencies import get_tenant_user_context
from app.models.base import ResponseModel
from app.models.flink_job_template import (
    JobTemplateCreate, FlinkJobSubmitRequest, FlinkJobControlRequest,
    JobTemplateType, JobStatus
)
from app.services.flink import get_flink_job_manager

router = APIRouter(prefix="/flink-jobs", tags=["Flink 作业管理"])


# ========== 作业模板管理 ==========

@router.post("/templates", response_model=ResponseModel)
async def create_job_template(
    template: JobTemplateCreate,
    context=Depends(get_tenant_user_context)
):
    """
    创建作业模板
    
    支持动态配置任意作业类型，不限于固定的3种作业
    """
    job_manager = get_flink_job_manager()
    
    try:
        created_template = await job_manager.create_job_template(template)
        
        return ResponseModel(
            message="模板创建成功",
            data=created_template.dict()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")


@router.get("/templates", response_model=ResponseModel)
async def list_job_templates(
    status: Optional[str] = Query(None, description="模板状态过滤"),
    context=Depends(get_tenant_user_context)
):
    """列出所有作业模板"""
    job_manager = get_flink_job_manager()
    
    templates = await job_manager.list_job_templates(status=status)
    
    return ResponseModel(
        message="查询成功",
        data={
            "templates": [t.dict() for t in templates],
            "total": len(templates)
        }
    )


@router.get("/templates/{template_id}", response_model=ResponseModel)
async def get_job_template(
    template_id: str,
    context=Depends(get_tenant_user_context)
):
    """获取作业模板"""
    job_manager = get_flink_job_manager()
    
    template = await job_manager.get_job_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return ResponseModel(
        message="查询成功",
        data=template.dict()
    )


# ========== 作业实例管理 ==========

@router.post("/submit", response_model=ResponseModel)
async def submit_job(
    request: FlinkJobSubmitRequest,
    context=Depends(get_tenant_user_context)
):
    """
    提交 Flink 作业
    
    通过 REST API 提交作业到 Flink 集群，而不是直接运行 Python 脚本
    """
    job_manager = get_flink_job_manager()
    
    try:
        flink_job = await job_manager.submit_job(
            request,
            submitted_by=context.get("user_id")
        )
        
        return ResponseModel(
            message="作业提交成功",
            data=flink_job.dict()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交作业失败: {str(e)}")


@router.get("/jobs", response_model=ResponseModel)
async def list_jobs(
    status: Optional[str] = Query(None, description="作业状态过滤"),
    context=Depends(get_tenant_user_context)
):
    """列出所有作业"""
    job_manager = get_flink_job_manager()
    
    jobs = await job_manager.list_jobs(status=status)
    
    return ResponseModel(
        message="查询成功",
        data={
            "jobs": [j.dict() for j in jobs],
            "total": len(jobs)
        }
    )


@router.get("/jobs/{job_id}", response_model=ResponseModel)
async def get_job(
    job_id: str,
    context=Depends(get_tenant_user_context)
):
    """获取作业信息（同步 Flink 集群状态）"""
    job_manager = get_flink_job_manager()
    
    job = await job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="作业不存在")
    
    return ResponseModel(
        message="查询成功",
        data=job.dict()
    )


@router.post("/jobs/{job_id}/stop", response_model=ResponseModel)
async def stop_job(
    job_id: str,
    force: bool = Query(False, description="是否强制停止"),
    context=Depends(get_tenant_user_context)
):
    """
    停止 Flink 作业
    
    通过 Flink REST API 停止作业，而不是直接杀死进程
    """
    job_manager = get_flink_job_manager()
    
    try:
        result = await job_manager.stop_job(job_id, force=force)
        
        return ResponseModel(
            message="作业已停止",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止作业失败: {str(e)}")


@router.post("/jobs/{job_id}/pause", response_model=ResponseModel)
async def pause_job(
    job_id: str,
    context=Depends(get_tenant_user_context)
):
    """
    暂停 Flink 作业（创建 Savepoint 并停止）
    
    通过 Flink REST API 暂停作业
    """
    job_manager = get_flink_job_manager()
    
    # TODO: 实现暂停功能（需要先获取 flink_job_id）
    raise HTTPException(status_code=501, detail="暂停功能待实现")


@router.post("/jobs/{job_id}/resume", response_model=ResponseModel)
async def resume_job(
    job_id: str,
    savepoint_path: Optional[str] = Query(None, description="Savepoint 路径"),
    context=Depends(get_tenant_user_context)
):
    """
    恢复 Flink 作业（从 Savepoint 恢复）
    
    通过重新提交作业并从 Savepoint 恢复
    """
    job_manager = get_flink_job_manager()
    
    # TODO: 实现恢复功能
    raise HTTPException(status_code=501, detail="恢复功能待实现")


# ========== Flink 集群信息 ==========

@router.get("/cluster/info", response_model=ResponseModel)
async def get_cluster_info(
    context=Depends(get_tenant_user_context)
):
    """获取 Flink 集群信息"""
    job_manager = get_flink_job_manager()
    
    try:
        info = await job_manager.get_cluster_info()
        
        return ResponseModel(
            message="查询成功",
            data=info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取集群信息失败: {str(e)}")


@router.get("/cluster/jobs", response_model=ResponseModel)
async def list_flink_cluster_jobs(
    context=Depends(get_tenant_user_context)
):
    """列出 Flink 集群中的所有作业"""
    job_manager = get_flink_job_manager()
    
    try:
        jobs = await job_manager.list_flink_jobs()
        
        return ResponseModel(
            message="查询成功",
            data={
                "jobs": jobs,
                "total": len(jobs)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出作业失败: {str(e)}")

