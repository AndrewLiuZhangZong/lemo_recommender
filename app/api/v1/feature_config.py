"""
实时特征配置API
配置实时特征计算规则
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.api.dependencies import get_tenant_user_context, get_mongodb
from app.models.base import ResponseModel


router = APIRouter()


class FeatureRule(BaseModel):
    """特征计算规则"""
    feature_name: str = Field(..., description="特征名称")
    feature_type: str = Field(..., description="特征类型: count, sum, avg, ratio, list")
    aggregation_window: str = Field(..., description="聚合窗口: 5m, 1h, 1d, 7d")
    source_field: str = Field(..., description="源字段")
    filter_condition: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    enabled: bool = Field(default=True, description="是否启用")


class FeatureConfigCreate(BaseModel):
    """创建特征配置"""
    scenario_id: str = Field(..., description="场景ID")
    config_name: str = Field(..., description="配置名称")
    description: Optional[str] = None
    feature_rules: List[FeatureRule] = Field(..., description="特征规则列表")


class FeatureConfigUpdate(BaseModel):
    """更新特征配置"""
    config_name: Optional[str] = None
    description: Optional[str] = None
    feature_rules: Optional[List[FeatureRule]] = None
    enabled: Optional[bool] = None


@router.post("")
async def create_feature_config(
    data: FeatureConfigCreate,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    创建实时特征配置
    """
    tenant_id = context["tenant_id"]
    
    # 验证场景是否存在
    scenario = db.scenarios.find_one({
        "tenant_id": tenant_id,
        "scenario_id": data.scenario_id
    })
    
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    # 创建配置
    config_doc = {
        "tenant_id": tenant_id,
        "scenario_id": data.scenario_id,
        "config_name": data.config_name,
        "description": data.description,
        "feature_rules": [r.dict() for r in data.feature_rules],
        "enabled": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = db.feature_configs.insert_one(config_doc)
    config_doc["_id"] = str(result.inserted_id)
    
    return ResponseModel(
        message="特征配置创建成功",
        data=config_doc
    )


@router.get("")
async def list_feature_configs(
    scenario_id: Optional[str] = None,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    查询特征配置列表
    """
    tenant_id = context["tenant_id"]
    
    query = {"tenant_id": tenant_id}
    if scenario_id:
        query["scenario_id"] = scenario_id
    
    configs = list(db.feature_configs.find(query).sort("created_at", -1))
    
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
async def get_feature_config(
    config_id: str,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    获取特征配置详情
    """
    from bson import ObjectId
    
    tenant_id = context["tenant_id"]
    
    try:
        config = db.feature_configs.find_one({
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
async def update_feature_config(
    config_id: str,
    data: FeatureConfigUpdate,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    更新特征配置
    """
    from bson import ObjectId
    
    tenant_id = context["tenant_id"]
    
    # 验证配置存在
    try:
        config = db.feature_configs.find_one({
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
    
    if data.feature_rules is not None:
        update_data["feature_rules"] = [r.dict() for r in data.feature_rules]
    
    if data.enabled is not None:
        update_data["enabled"] = data.enabled
    
    # 更新配置
    db.feature_configs.update_one(
        {"_id": ObjectId(config_id)},
        {"$set": update_data}
    )
    
    return ResponseModel(
        message="更新成功",
        data={"config_id": config_id}
    )


@router.delete("/{config_id}")
async def delete_feature_config(
    config_id: str,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    删除特征配置
    """
    from bson import ObjectId
    
    tenant_id = context["tenant_id"]
    
    try:
        result = db.feature_configs.delete_one({
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


@router.get("/features/available")
async def get_available_features():
    """
    获取可配置的特征类型列表
    """
    features = [
        {
            "category": "用户行为统计",
            "features": [
                {
                    "feature_name": "user_view_count_5m",
                    "display_name": "5分钟浏览次数",
                    "feature_type": "count",
                    "aggregation_window": "5m",
                    "source_field": "action_type",
                    "filter_condition": {"action_type": "view"}
                },
                {
                    "feature_name": "user_click_count_1h",
                    "display_name": "1小时点击次数",
                    "feature_type": "count",
                    "aggregation_window": "1h",
                    "source_field": "action_type",
                    "filter_condition": {"action_type": "click"}
                },
                {
                    "feature_name": "user_like_count_1d",
                    "display_name": "24小时点赞次数",
                    "feature_type": "count",
                    "aggregation_window": "1d",
                    "source_field": "action_type",
                    "filter_condition": {"action_type": "like"}
                }
            ]
        },
        {
            "category": "用户偏好",
            "features": [
                {
                    "feature_name": "user_favorite_categories",
                    "display_name": "偏好分类列表",
                    "feature_type": "list",
                    "aggregation_window": "7d",
                    "source_field": "item.category",
                    "filter_condition": {"action_type": {"$in": ["like", "favorite"]}}
                },
                {
                    "feature_name": "user_favorite_tags",
                    "display_name": "偏好标签列表",
                    "feature_type": "list",
                    "aggregation_window": "7d",
                    "source_field": "item.tags",
                    "filter_condition": {"action_type": {"$in": ["like", "favorite"]}}
                }
            ]
        },
        {
            "category": "用户活跃度",
            "features": [
                {
                    "feature_name": "user_avg_watch_duration",
                    "display_name": "平均观看时长",
                    "feature_type": "avg",
                    "aggregation_window": "1h",
                    "source_field": "context.watch_duration",
                    "filter_condition": {"action_type": "view"}
                },
                {
                    "feature_name": "user_engagement_rate",
                    "display_name": "互动率",
                    "feature_type": "ratio",
                    "aggregation_window": "1h",
                    "source_field": "action_type",
                    "filter_condition": {}
                }
            ]
        },
        {
            "category": "物品统计",
            "features": [
                {
                    "feature_name": "item_view_count_1h",
                    "display_name": "物品1小时浏览量",
                    "feature_type": "count",
                    "aggregation_window": "1h",
                    "source_field": "item_id",
                    "filter_condition": {"action_type": "view"}
                },
                {
                    "feature_name": "item_click_rate",
                    "display_name": "物品点击率",
                    "feature_type": "ratio",
                    "aggregation_window": "1h",
                    "source_field": "action_type",
                    "filter_condition": {}
                }
            ]
        }
    ]
    
    return ResponseModel(
        message="查询成功",
        data={"features": features}
    )


@router.post("/{config_id}/deploy")
async def deploy_feature_config(
    config_id: str,
    context = Depends(get_tenant_user_context),
    db = Depends(get_mongodb)
):
    """
    部署特征配置到Flink作业
    """
    from bson import ObjectId
    
    tenant_id = context["tenant_id"]
    
    try:
        config = db.feature_configs.find_one({
            "_id": ObjectId(config_id),
            "tenant_id": tenant_id
        })
    except Exception:
        raise HTTPException(status_code=400, detail="无效的配置ID")
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # TODO: 将配置部署到Flink作业
    # 1. 生成Flink作业配置
    # 2. 重启相关Flink作业
    # 3. 验证部署结果
    
    # 更新部署状态
    db.feature_configs.update_one(
        {"_id": ObjectId(config_id)},
        {
            "$set": {
                "deployed": True,
                "deployed_at": datetime.utcnow()
            }
        }
    )
    
    return ResponseModel(
        message="特征配置已部署",
        data={"config_id": config_id}
    )

