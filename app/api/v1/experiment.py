"""
AB实验管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.models.experiment import (
    Experiment,
    ExperimentStatus,
    ExperimentResult
)
from app.services.experiment.service import ExperimentService
from app.api.dependencies import get_mongodb, get_tenant_user_context


router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=Experiment, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    experiment: Experiment,
    db=Depends(get_mongodb),
    context=Depends(get_tenant_user_context)
):
    """
    创建AB实验
    
    请求体示例:
    ```json
    {
      "experiment_id": "exp_vector_recall_001",
      "tenant_id": "demo_tenant",
      "scenario_id": "vlog_main_feed",
      "name": "向量召回实验",
      "description": "测试向量召回对CTR的提升效果",
      "hypothesis": "向量召回能提升CTR 5%以上",
      "traffic_split_method": "user_id_hash",
      "variants": [
        {
          "variant_id": "control",
          "name": "对照组-协同过滤",
          "traffic_percentage": 50,
          "recall_strategy": {"collaborative_filtering": {"weight": 1.0}}
        },
        {
          "variant_id": "treatment",
          "name": "实验组-向量召回",
          "traffic_percentage": 50,
          "recall_strategy": {"vector_search": {"weight": 1.0}}
        }
      ],
      "metrics": {
        "primary_metric": "ctr",
        "secondary_metrics": ["avg_watch_duration", "engagement_rate"],
        "guardrail_metrics": [
          {"name": "coverage", "threshold": 0.5, "direction": ">="}
        ]
      },
      "min_sample_size": 5000,
      "confidence_level": 0.95,
      "created_by": "admin@example.com"
    }
    ```
    """
    service = ExperimentService(db)
    
    try:
        experiment = await service.create_experiment(experiment)
        return experiment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[Experiment])
async def list_experiments(
    scenario_id: Optional[str] = None,
    status: Optional[ExperimentStatus] = None,
    db=Depends(get_mongodb),
    context=Depends(get_tenant_user_context)
):
    """列出AB实验"""
    service = ExperimentService(db)
    tenant_id = context["tenant_id"]
    
    experiments = await service.list_experiments(
        tenant_id=tenant_id,
        scenario_id=scenario_id,
        status=status
    )
    
    return experiments


@router.get("/{experiment_id}", response_model=Experiment)
async def get_experiment(
    experiment_id: str,
    db=Depends(get_mongodb),
    context=Depends(get_tenant_user_context)
):
    """获取实验详情"""
    service = ExperimentService(db)
    tenant_id = context["tenant_id"]
    
    experiment = await service.get_experiment(tenant_id, experiment_id)
    
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    
    return experiment


@router.post("/{experiment_id}/start", response_model=Experiment)
async def start_experiment(
    experiment_id: str,
    db=Depends(get_mongodb),
    context=Depends(get_tenant_user_context)
):
    """启动实验"""
    service = ExperimentService(db)
    tenant_id = context["tenant_id"]
    
    try:
        experiment = await service.start_experiment(tenant_id, experiment_id)
        return experiment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{experiment_id}/stop", response_model=Experiment)
async def stop_experiment(
    experiment_id: str,
    db=Depends(get_mongodb),
    context=Depends(get_tenant_user_context)
):
    """停止实验"""
    service = ExperimentService(db)
    tenant_id = context["tenant_id"]
    
    try:
        experiment = await service.stop_experiment(tenant_id, experiment_id)
        return experiment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{experiment_id}/results", response_model=List[ExperimentResult])
async def get_experiment_results(
    experiment_id: str,
    db=Depends(get_mongodb),
    context=Depends(get_tenant_user_context)
):
    """
    获取实验结果
    
    返回示例:
    ```json
    [
      {
        "experiment_id": "exp_001",
        "variant_id": "control",
        "sample_size": 5234,
        "metrics": {
          "ctr": 0.0456,
          "avg_watch_duration": 42.3,
          "engagement_rate": 0.112
        },
        "is_significant": false,
        "p_value": 1.0,
        "confidence_interval": [0.0, 0.0],
        "lift": {}
      },
      {
        "experiment_id": "exp_001",
        "variant_id": "treatment",
        "sample_size": 5189,
        "metrics": {
          "ctr": 0.0492,
          "avg_watch_duration": 45.1,
          "engagement_rate": 0.125
        },
        "is_significant": true,
        "p_value": 0.021,
        "confidence_interval": [0.002, 0.008],
        "lift": {
          "ctr": 7.89,
          "avg_watch_duration": 6.62,
          "engagement_rate": 11.61
        }
      }
    ]
    ```
    """
    service = ExperimentService(db)
    tenant_id = context["tenant_id"]
    
    try:
        results = await service.compute_experiment_results(tenant_id, experiment_id)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{experiment_id}/assign")
async def assign_user_to_variant(
    experiment_id: str,
    user_id: str,
    db=Depends(get_mongodb),
    context=Depends(get_tenant_user_context)
):
    """
    为用户分配实验变体
    
    用于测试或手动分配
    """
    service = ExperimentService(db)
    tenant_id = context["tenant_id"]
    
    experiment = await service.get_experiment(tenant_id, experiment_id)
    
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    
    variant_id = service.assign_variant(experiment, user_id)
    
    await service.record_assignment(tenant_id, experiment_id, user_id, variant_id)
    
    return {
        "experiment_id": experiment_id,
        "user_id": user_id,
        "variant_id": variant_id
    }

