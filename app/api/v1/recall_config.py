"""
召回策略配置API
可视化配置标签、作者、分类等召回策略权重
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.api.dependencies import get_tenant_user_context, get_mongodb
from app.models.base import ResponseModel


router = APIRouter()


class RecallStrategyWeight(BaseModel):
    """召回策略权重"""
    strategy: str = Field(..., description="策略名称")
    weight: float = Field(..., ge=0, le=1, description="权重（0-1）")
    enabled: bool = Field(default=True, description="是否启用")
    params: Dict[str, Any] = Field(default={}, description="策略参数")


class RecallConfigCreate(BaseModel):
    """创建召回配置"""
    scenario_id: str = Field(..., description="场景ID")
    config_name: str = Field(..., description="配置名称")
    description: Optional[str] = Field(None, description="描述")
    strategies: List[RecallStrategyWeight] = Field(..., description="召回策略列表")
    is_default: bool = Field(default=False, description="是否为默认配置")


class RecallConfigUpdate(BaseModel):
    """更新召回配置"""
    config_name: Optional[str] = None
    description: Optional[str] = None
    strategies: Optional[List[RecallStrategyWeight]] = None
    is_default: Optional[bool] = None
    enabled: Optional[bool] = None


@router.post("")
async def create_recall_config(
    data: RecallConfigCreate,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    创建召回策略配置
    """
    tenant_id = context["tenant_id"]
    
    # 验证场景是否存在
    scenario = db.scenarios.find_one({
        "tenant_id": tenant_id,
        "scenario_id": data.scenario_id
    })
    
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    # 验证权重总和是否为1
    total_weight = sum(s.weight for s in data.strategies if s.enabled)
    if abs(total_weight - 1.0) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"启用策略的权重总和必须为1，当前为{total_weight:.2f}"
        )
    
    # 如果设置为默认，取消其他默认配置
    if data.is_default:
        db.recall_configs.update_many(
            {
                "tenant_id": tenant_id,
                "scenario_id": data.scenario_id,
                "is_default": True
            },
            {"$set": {"is_default": False}}
        )
    
    # 创建配置
    config_doc = {
        "tenant_id": tenant_id,
        "scenario_id": data.scenario_id,
        "config_name": data.config_name,
        "description": data.description,
        "strategies": [s.dict() for s in data.strategies],
        "is_default": data.is_default,
        "enabled": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = db.recall_configs.insert_one(config_doc)
    config_doc["_id"] = str(result.inserted_id)
    
    return ResponseModel(
        message="召回配置创建成功",
        data=config_doc
    )


@router.get("")
async def list_recall_configs(
    scenario_id: Optional[str] = None,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    查询召回配置列表
    """
    tenant_id = context["tenant_id"]
    
    query = {"tenant_id": tenant_id}
    if scenario_id:
        query["scenario_id"] = scenario_id
    
    configs = list(db.recall_configs.find(query).sort("created_at", -1))
    
    for config in configs:
        config["_id"] = str(config["_id"])
        if "created_at" in config:
            config["created_at"] = config["created_at"].isoformat()
        if "updated_at" in config:
            config["updated_at"] = config["updated_at"].isoformat()
    
    return ResponseModel(
        message="查询成功",
        data={"configs": configs, "total": len(configs)}
    )


@router.get("/{config_id}")
async def get_recall_config(
    config_id: str,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    获取召回配置详情
    """
    from bson import ObjectId
    
    tenant_id = context["tenant_id"]
    
    try:
        config = db.recall_configs.find_one({
            "_id": ObjectId(config_id),
            "tenant_id": tenant_id
        })
    except Exception:
        raise HTTPException(status_code=400, detail="无效的配置ID")
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    config["_id"] = str(config["_id"])
    if "created_at" in config:
        config["created_at"] = config["created_at"].isoformat()
    if "updated_at" in config:
        config["updated_at"] = config["updated_at"].isoformat()
    
    return ResponseModel(
        message="查询成功",
        data=config
    )


@router.put("/{config_id}")
async def update_recall_config(
    config_id: str,
    data: RecallConfigUpdate,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    更新召回配置
    """
    from bson import ObjectId
    
    tenant_id = context["tenant_id"]
    
    # 验证配置存在
    try:
        config = db.recall_configs.find_one({
            "_id": ObjectId(config_id),
            "tenant_id": tenant_id
        })
    except Exception:
        raise HTTPException(status_code=400, detail="无效的配置ID")
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 构建更新数据
    update_data = {"updated_at": datetime.utcnow()}
    
    if data.config_name is not None:
        update_data["config_name"] = data.config_name
    
    if data.description is not None:
        update_data["description"] = data.description
    
    if data.strategies is not None:
        # 验证权重
        total_weight = sum(s.weight for s in data.strategies if s.enabled)
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"启用策略的权重总和必须为1，当前为{total_weight:.2f}"
            )
        update_data["strategies"] = [s.dict() for s in data.strategies]
    
    if data.is_default is not None:
        if data.is_default:
            # 取消其他默认配置
            db.recall_configs.update_many(
                {
                    "tenant_id": tenant_id,
                    "scenario_id": config["scenario_id"],
                    "is_default": True
                },
                {"$set": {"is_default": False}}
            )
        update_data["is_default"] = data.is_default
    
    if data.enabled is not None:
        update_data["enabled"] = data.enabled
    
    # 更新配置
    db.recall_configs.update_one(
        {"_id": ObjectId(config_id)},
        {"$set": update_data}
    )
    
    return ResponseModel(
        message="更新成功",
        data={"config_id": config_id}
    )


@router.delete("/{config_id}")
async def delete_recall_config(
    config_id: str,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    删除召回配置
    """
    from bson import ObjectId
    
    tenant_id = context["tenant_id"]
    
    try:
        result = db.recall_configs.delete_one({
            "_id": ObjectId(config_id),
            "tenant_id": tenant_id
        })
    except Exception:
        raise HTTPException(status_code=400, detail="无效的配置ID")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return ResponseModel(
        message="删除成功",
        data={"config_id": config_id}
    )


@router.get("/strategies/available")
async def get_available_strategies():
    """
    获取可用的召回策略列表
    """
    strategies = [
        {
            "strategy": "hot_items",
            "name": "热门物品召回",
            "description": "基于物品热度排序召回",
            "default_weight": 0.3,
            "params": {
                "time_decay": {
                    "type": "float",
                    "default": 0.1,
                    "description": "时间衰减系数"
                },
                "min_score": {
                    "type": "float",
                    "default": 0.0,
                    "description": "最低热度分数"
                }
            }
        },
        {
            "strategy": "collaborative_filtering",
            "name": "协同过滤召回",
            "description": "基于用户行为的协同过滤",
            "default_weight": 0.3,
            "params": {
                "similarity_method": {
                    "type": "select",
                    "options": ["cosine", "pearson", "jaccard"],
                    "default": "cosine",
                    "description": "相似度计算方法"
                },
                "min_similarity": {
                    "type": "float",
                    "default": 0.1,
                    "description": "最低相似度"
                }
            }
        },
        {
            "strategy": "vector_search",
            "name": "向量召回",
            "description": "基于embedding向量相似度",
            "default_weight": 0.2,
            "params": {
                "metric": {
                    "type": "select",
                    "options": ["cosine", "euclidean", "dot_product"],
                    "default": "cosine",
                    "description": "距离度量"
                },
                "top_k": {
                    "type": "int",
                    "default": 500,
                    "description": "召回数量"
                }
            }
        },
        {
            "strategy": "tag_based",
            "name": "标签召回",
            "description": "基于物品标签匹配",
            "default_weight": 0.1,
            "params": {
                "match_threshold": {
                    "type": "float",
                    "default": 0.3,
                    "description": "匹配阈值"
                },
                "tag_weights": {
                    "type": "dict",
                    "default": {},
                    "description": "标签权重映射"
                }
            }
        },
        {
            "strategy": "author_based",
            "name": "作者召回",
            "description": "基于用户关注的作者",
            "default_weight": 0.05,
            "params": {
                "author_recent_days": {
                    "type": "int",
                    "default": 7,
                    "description": "作者最近N天的内容"
                },
                "min_author_score": {
                    "type": "float",
                    "default": 0.0,
                    "description": "作者最低评分"
                }
            }
        },
        {
            "strategy": "category_based",
            "name": "分类召回",
            "description": "基于用户偏好分类",
            "default_weight": 0.05,
            "params": {
                "category_weights": {
                    "type": "dict",
                    "default": {},
                    "description": "分类权重"
                },
                "diversity_factor": {
                    "type": "float",
                    "default": 0.3,
                    "description": "多样性因子"
                }
            }
        }
    ]
    
    return ResponseModel(
        message="查询成功",
        data={"strategies": strategies}
    )


@router.post("/{config_id}/clone")
async def clone_recall_config(
    config_id: str,
    new_name: str,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    克隆召回配置
    """
    from bson import ObjectId
    
    tenant_id = context["tenant_id"]
    
    # 获取原配置
    try:
        config = db.recall_configs.find_one({
            "_id": ObjectId(config_id),
            "tenant_id": tenant_id
        })
    except Exception:
        raise HTTPException(status_code=400, detail="无效的配置ID")
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 创建新配置
    del config["_id"]
    config["config_name"] = new_name
    config["is_default"] = False
    config["created_at"] = datetime.utcnow()
    config["updated_at"] = datetime.utcnow()
    
    result = db.recall_configs.insert_one(config)
    config["_id"] = str(result.inserted_id)
    
    return ResponseModel(
        message="克隆成功",
        data=config
    )

