"""
模型训练管理API
支持一键触发Wide&Deep、DeepFM、Two-Tower模型训练
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.api.dependencies import get_tenant_user_context, get_mongodb
from app.models.base import ResponseModel
from app.tasks.model_tasks import train_model_daily


router = APIRouter()


class ModelTrainRequest(BaseModel):
    """模型训练请求"""
    model_type: str = Field(..., description="模型类型: wide_deep, deepfm, two_tower")
    scenario_id: str = Field(..., description="场景ID")
    config: Optional[dict] = Field(default={}, description="训练配置")


class ModelTrainStatus(BaseModel):
    """模型训练状态"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: Optional[float] = None
    message: Optional[str] = None


@router.post("/train")
async def trigger_model_training(
    request: ModelTrainRequest,
    background_tasks: BackgroundTasks,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    一键触发模型训练
    
    支持的模型类型:
    - wide_deep: Wide & Deep模型
    - deepfm: DeepFM模型
    - two_tower: 双塔模型（用于向量召回）
    """
    tenant_id = context["tenant_id"]
    
    # 验证场景是否存在
    scenario = db.scenarios.find_one({
        "tenant_id": tenant_id,
        "scenario_id": request.scenario_id
    })
    
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    # 验证模型类型
    valid_models = ["wide_deep", "deepfm", "two_tower"]
    if request.model_type not in valid_models:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模型类型，支持: {', '.join(valid_models)}"
        )
    
    try:
        # 触发Celery异步训练任务
        task = train_model_daily.delay(
            tenant_id=tenant_id,
            scenario_id=request.scenario_id,
            model_type=request.model_type,
            config=request.config or {}
        )
        
        # 记录训练任务到MongoDB
        training_record = {
            "task_id": task.id,
            "tenant_id": tenant_id,
            "scenario_id": request.scenario_id,
            "model_type": request.model_type,
            "config": request.config,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        db.model_training_tasks.insert_one(training_record)
        
        return ResponseModel(
            message="模型训练任务已提交",
            data={
                "task_id": task.id,
                "model_type": request.model_type,
                "scenario_id": request.scenario_id,
                "status": "pending"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"启动训练失败: {str(e)}"
        )


@router.get("/tasks")
async def list_training_tasks(
    scenario_id: Optional[str] = None,
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    查询训练任务列表
    """
    tenant_id = context["tenant_id"]
    
    # 构建查询条件
    query = {"tenant_id": tenant_id}
    if scenario_id:
        query["scenario_id"] = scenario_id
    if model_type:
        query["model_type"] = model_type
    if status:
        query["status"] = status
    
    # 查询任务
    tasks = list(
        db.model_training_tasks
        .find(query)
        .sort("created_at", -1)
        .limit(limit)
    )
    
    # 转换格式
    for task in tasks:
        task["_id"] = str(task["_id"])
        if "created_at" in task:
            task["created_at"] = task["created_at"].isoformat()
        if "updated_at" in task:
            task["updated_at"] = task["updated_at"].isoformat()
    
    return ResponseModel(
        message="查询成功",
        data={
            "tasks": tasks,
            "total": len(tasks)
        }
    )


@router.get("/tasks/{task_id}")
async def get_training_task_status(
    task_id: str,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    查询训练任务状态
    """
    tenant_id = context["tenant_id"]
    
    # 从MongoDB查询任务记录
    task = db.model_training_tasks.find_one({
        "task_id": task_id,
        "tenant_id": tenant_id
    })
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 从Celery查询实时状态
    from app.tasks.celery_app import celery_app
    celery_task = celery_app.AsyncResult(task_id)
    
    # 更新状态
    if celery_task.state == "SUCCESS":
        task["status"] = "completed"
        task["result"] = celery_task.result
    elif celery_task.state == "FAILURE":
        task["status"] = "failed"
        task["error"] = str(celery_task.result)
    elif celery_task.state == "PENDING":
        task["status"] = "pending"
    elif celery_task.state == "STARTED":
        task["status"] = "running"
    
    # 格式化
    task["_id"] = str(task["_id"])
    if "created_at" in task:
        task["created_at"] = task["created_at"].isoformat()
    if "updated_at" in task:
        task["updated_at"] = task["updated_at"].isoformat()
    
    return ResponseModel(
        message="查询成功",
        data=task
    )


@router.delete("/tasks/{task_id}")
async def cancel_training_task(
    task_id: str,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    取消训练任务
    """
    tenant_id = context["tenant_id"]
    
    # 验证任务存在
    task = db.model_training_tasks.find_one({
        "task_id": task_id,
        "tenant_id": tenant_id
    })
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 取消Celery任务
    from app.tasks.celery_app import celery_app
    celery_app.control.revoke(task_id, terminate=True)
    
    # 更新状态
    db.model_training_tasks.update_one(
        {"task_id": task_id},
        {
            "$set": {
                "status": "cancelled",
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return ResponseModel(
        message="任务已取消",
        data={"task_id": task_id}
    )


@router.get("/models/types")
async def get_model_types():
    """
    获取支持的模型类型列表
    """
    model_types = [
        {
            "value": "wide_deep",
            "label": "Wide & Deep",
            "description": "结合Wide（记忆能力）和Deep（泛化能力）的经典模型",
            "use_case": "适用于电商、新闻等场景"
        },
        {
            "value": "deepfm",
            "label": "DeepFM",
            "description": "集成FM和DNN的点击率预估模型",
            "use_case": "适用于广告、推荐等点击率预估场景"
        },
        {
            "value": "two_tower",
            "label": "Two-Tower（双塔）",
            "description": "用户塔和物品塔分别编码，用于向量召回",
            "use_case": "适用于大规模向量召回场景"
        }
    ]
    
    return ResponseModel(
        message="查询成功",
        data={"types": model_types}
    )


@router.get("/config/template")
async def get_training_config_template(
    model_type: str
):
    """
    获取训练配置模板
    """
    templates = {
        "wide_deep": {
            "epochs": 10,
            "batch_size": 256,
            "learning_rate": 0.001,
            "wide_dim": 100,
            "deep_dims": [512, 256, 128],
            "dropout": 0.2
        },
        "deepfm": {
            "epochs": 10,
            "batch_size": 256,
            "learning_rate": 0.001,
            "embedding_dim": 32,
            "deep_dims": [256, 128, 64],
            "dropout": 0.2
        },
        "two_tower": {
            "epochs": 10,
            "batch_size": 512,
            "learning_rate": 0.001,
            "embedding_dim": 128,
            "user_tower_dims": [256, 128],
            "item_tower_dims": [256, 128],
            "temperature": 0.05
        }
    }
    
    if model_type not in templates:
        raise HTTPException(status_code=404, detail="模型类型不存在")
    
    return ResponseModel(
        message="查询成功",
        data=templates[model_type]
    )

