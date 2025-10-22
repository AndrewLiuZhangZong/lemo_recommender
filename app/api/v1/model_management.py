"""
排序模型管理API
上传、部署、切换排序模型
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import hashlib

from app.api.dependencies import get_tenant_user_context, get_mongodb
from app.models.base import ResponseModel


router = APIRouter()


class ModelDeploy(BaseModel):
    """部署模型"""
    model_id: str = Field(..., description="模型ID")
    scenario_id: str = Field(..., description="场景ID")


class ModelSwitch(BaseModel):
    """切换模型"""
    scenario_id: str = Field(..., description="场景ID")
    model_id: str = Field(..., description="要切换到的模型ID")


@router.get("/list")
async def list_models(
    scenario_id: Optional[str] = None,
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    查询模型列表
    
    Args:
        scenario_id: 场景ID（可选）
        model_type: 模型类型（可选）
        status: 状态（可选: trained, deployed, archived）
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
    
    # 查询模型
    models = list(db.trained_models.find(query).sort("trained_at", -1))
    
    # 转换格式
    for model in models:
        model["_id"] = str(model["_id"])
        if "trained_at" in model:
            model["trained_at"] = model["trained_at"].isoformat()
        if "deployed_at" in model:
            model["deployed_at"] = model["deployed_at"].isoformat()
    
    return ResponseModel(
        message="查询成功",
        data={"models": models, "total": len(models)}
    )


@router.get("/{model_id}")
async def get_model_detail(
    model_id: str,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    获取模型详情
    """
    from bson import ObjectId
    
    tenant_id = context["tenant_id"]
    
    try:
        model = db.trained_models.find_one({
            "_id": ObjectId(model_id),
            "tenant_id": tenant_id
        })
    except Exception:
        raise HTTPException(status_code=400, detail="无效的模型ID")
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    model["_id"] = str(model["_id"])
    if "trained_at" in model:
        model["trained_at"] = model["trained_at"].isoformat()
    if "deployed_at" in model:
        model["deployed_at"] = model["deployed_at"].isoformat()
    
    return ResponseModel(
        message="查询成功",
        data=model
    )


@router.post("/upload")
async def upload_model(
    scenario_id: str,
    model_type: str,
    model_name: str,
    description: Optional[str] = None,
    file: UploadFile = File(...),
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    上传模型文件
    
    Args:
        scenario_id: 场景ID
        model_type: 模型类型
        model_name: 模型名称
        description: 描述
        file: 模型文件
    """
    tenant_id = context["tenant_id"]
    
    # 验证场景是否存在
    scenario = db.scenarios.find_one({
        "tenant_id": tenant_id,
        "scenario_id": scenario_id
    })
    
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    # 读取文件内容
    file_content = await file.read()
    file_size = len(file_content)
    
    # 计算文件哈希
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # 这里应该保存文件到对象存储（如MinIO、OSS）
    # 简化起见，这里只记录元数据
    file_path = f"models/{tenant_id}/{scenario_id}/{file_hash}_{file.filename}"
    
    # 创建模型记录
    model_doc = {
        "tenant_id": tenant_id,
        "scenario_id": scenario_id,
        "model_type": model_type,
        "model_name": model_name,
        "description": description,
        "file_name": file.filename,
        "file_path": file_path,
        "file_size": file_size,
        "file_hash": file_hash,
        "status": "uploaded",
        "uploaded_at": datetime.utcnow(),
        "metrics": {},
        "config": {}
    }
    
    result = db.trained_models.insert_one(model_doc)
    model_doc["_id"] = str(result.inserted_id)
    
    return ResponseModel(
        message="模型上传成功",
        data=model_doc
    )


@router.post("/deploy")
async def deploy_model(
    data: ModelDeploy,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    部署模型到线上环境
    """
    from bson import ObjectId
    
    tenant_id = context["tenant_id"]
    
    # 验证模型存在
    try:
        model = db.trained_models.find_one({
            "_id": ObjectId(data.model_id),
            "tenant_id": tenant_id
        })
    except Exception:
        raise HTTPException(status_code=400, detail="无效的模型ID")
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 更新模型状态为已部署
    db.trained_models.update_one(
        {"_id": ObjectId(data.model_id)},
        {
            "$set": {
                "status": "deployed",
                "deployed_at": datetime.utcnow()
            }
        }
    )
    
    # 记录部署历史
    deployment_record = {
        "tenant_id": tenant_id,
        "scenario_id": data.scenario_id,
        "model_id": data.model_id,
        "model_type": model["model_type"],
        "model_name": model.get("model_name", ""),
        "deployed_at": datetime.utcnow(),
        "deployed_by": context.get("user_id", "system")
    }
    
    db.model_deployments.insert_one(deployment_record)
    
    return ResponseModel(
        message="模型部署成功",
        data={"model_id": data.model_id}
    )


@router.post("/switch")
async def switch_model(
    data: ModelSwitch,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    切换场景的在线模型
    """
    from bson import ObjectId
    
    tenant_id = context["tenant_id"]
    
    # 验证场景存在
    scenario = db.scenarios.find_one({
        "tenant_id": tenant_id,
        "scenario_id": data.scenario_id
    })
    
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    # 验证模型存在且已部署
    try:
        model = db.trained_models.find_one({
            "_id": ObjectId(data.model_id),
            "tenant_id": tenant_id,
            "status": "deployed"
        })
    except Exception:
        raise HTTPException(status_code=400, detail="无效的模型ID")
    
    if not model:
        raise HTTPException(
            status_code=404,
            detail="模型不存在或未部署"
        )
    
    # 获取当前在线模型
    current_model_id = scenario.get("online_model_id")
    
    # 更新场景的在线模型
    db.scenarios.update_one(
        {
            "tenant_id": tenant_id,
            "scenario_id": data.scenario_id
        },
        {
            "$set": {
                "online_model_id": data.model_id,
                "online_model_updated_at": datetime.utcnow()
            }
        }
    )
    
    # 记录切换历史
    switch_record = {
        "tenant_id": tenant_id,
        "scenario_id": data.scenario_id,
        "from_model_id": current_model_id,
        "to_model_id": data.model_id,
        "switched_at": datetime.utcnow(),
        "switched_by": context.get("user_id", "system")
    }
    
    db.model_switches.insert_one(switch_record)
    
    return ResponseModel(
        message="模型切换成功",
        data={
            "scenario_id": data.scenario_id,
            "from_model_id": current_model_id,
            "to_model_id": data.model_id
        }
    )


@router.post("/{model_id}/archive")
async def archive_model(
    model_id: str,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    归档模型（下线）
    """
    from bson import ObjectId
    
    tenant_id = context["tenant_id"]
    
    try:
        model = db.trained_models.find_one({
            "_id": ObjectId(model_id),
            "tenant_id": tenant_id
        })
    except Exception:
        raise HTTPException(status_code=400, detail="无效的模型ID")
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 检查是否有场景正在使用此模型
    using_scenarios = list(db.scenarios.find({
        "tenant_id": tenant_id,
        "online_model_id": model_id
    }))
    
    if using_scenarios:
        scenario_ids = [s["scenario_id"] for s in using_scenarios]
        raise HTTPException(
            status_code=400,
            detail=f"模型正在被以下场景使用，无法归档: {', '.join(scenario_ids)}"
        )
    
    # 更新状态为归档
    db.trained_models.update_one(
        {"_id": ObjectId(model_id)},
        {
            "$set": {
                "status": "archived",
                "archived_at": datetime.utcnow()
            }
        }
    )
    
    return ResponseModel(
        message="模型已归档",
        data={"model_id": model_id}
    )


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    删除模型
    """
    from bson import ObjectId
    
    tenant_id = context["tenant_id"]
    
    try:
        model = db.trained_models.find_one({
            "_id": ObjectId(model_id),
            "tenant_id": tenant_id
        })
    except Exception:
        raise HTTPException(status_code=400, detail="无效的模型ID")
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 检查是否有场景正在使用此模型
    using_scenarios = list(db.scenarios.find({
        "tenant_id": tenant_id,
        "online_model_id": model_id
    }))
    
    if using_scenarios:
        scenario_ids = [s["scenario_id"] for s in using_scenarios]
        raise HTTPException(
            status_code=400,
            detail=f"模型正在被以下场景使用，无法删除: {', '.join(scenario_ids)}"
        )
    
    # 删除模型
    db.trained_models.delete_one({"_id": ObjectId(model_id)})
    
    # TODO: 删除对象存储中的模型文件
    
    return ResponseModel(
        message="模型已删除",
        data={"model_id": model_id}
    )


@router.get("/history/deployments")
async def get_deployment_history(
    scenario_id: Optional[str] = None,
    limit: int = 50,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    查询部署历史
    """
    tenant_id = context["tenant_id"]
    
    query = {"tenant_id": tenant_id}
    if scenario_id:
        query["scenario_id"] = scenario_id
    
    deployments = list(
        db.model_deployments
        .find(query)
        .sort("deployed_at", -1)
        .limit(limit)
    )
    
    for d in deployments:
        d["_id"] = str(d["_id"])
        if "deployed_at" in d:
            d["deployed_at"] = d["deployed_at"].isoformat()
    
    return ResponseModel(
        message="查询成功",
        data={"deployments": deployments, "total": len(deployments)}
    )


@router.get("/history/switches")
async def get_switch_history(
    scenario_id: Optional[str] = None,
    limit: int = 50,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    查询切换历史
    """
    tenant_id = context["tenant_id"]
    
    query = {"tenant_id": tenant_id}
    if scenario_id:
        query["scenario_id"] = scenario_id
    
    switches = list(
        db.model_switches
        .find(query)
        .sort("switched_at", -1)
        .limit(limit)
    )
    
    for s in switches:
        s["_id"] = str(s["_id"])
        if "switched_at" in s:
            s["switched_at"] = s["switched_at"].isoformat()
    
    return ResponseModel(
        message="查询成功",
        data={"switches": switches, "total": len(switches)}
    )

