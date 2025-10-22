"""
管理后台API
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from app.api.dependencies import get_mongodb, get_tenant_user_context


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    scenario_id: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
    db=Depends(get_mongodb),
    context=Depends(get_tenant_user_context)
):
    """
    获取仪表板概览数据
    
    返回最近N天的核心指标
    """
    tenant_id = context["tenant_id"]
    start_time = datetime.utcnow() - timedelta(days=days)
    
    # 构建查询条件
    query = {
        "tenant_id": tenant_id,
        "timestamp": {"$gte": start_time}
    }
    if scenario_id:
        query["scenario_id"] = scenario_id
    
    # 1. 推荐请求量
    recommendation_count = await db.interactions.count_documents({
        **query,
        "action_type": "impression"
    })
    
    # 2. 点击量
    click_count = await db.interactions.count_documents({
        **query,
        "action_type": "click"
    })
    
    # 3. CTR
    ctr = click_count / recommendation_count if recommendation_count > 0 else 0
    
    # 4. 活跃用户数
    active_users = len(await db.interactions.distinct("user_id", query))
    
    # 5. 物品总数
    item_query = {"tenant_id": tenant_id}
    if scenario_id:
        item_query["scenario_id"] = scenario_id
    total_items = await db.items.count_documents(item_query)
    
    # 6. 场景数
    scenario_count = await db.scenarios.count_documents({"tenant_id": tenant_id})
    
    return {
        "tenant_id": tenant_id,
        "scenario_id": scenario_id,
        "period_days": days,
        "metrics": {
            "recommendation_count": recommendation_count,
            "click_count": click_count,
            "ctr": round(ctr, 4),
            "active_users": active_users,
            "total_items": total_items,
            "scenario_count": scenario_count
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/dashboard/trends")
async def get_metrics_trends(
    scenario_id: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
    db=Depends(get_mongodb),
    context=Depends(get_tenant_user_context)
):
    """获取指标趋势（按天聚合）"""
    tenant_id = context["tenant_id"]
    start_time = datetime.utcnow() - timedelta(days=days)
    
    query = {
        "tenant_id": tenant_id,
        "timestamp": {"$gte": start_time}
    }
    if scenario_id:
        query["scenario_id"] = scenario_id
    
    # 按天聚合
    pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "action_type": "$action_type"
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id.date": 1}}
    ]
    
    results = await db.interactions.aggregate(pipeline).to_list(length=None)
    
    # 格式化数据
    trends = {}
    for result in results:
        date = result["_id"]["date"]
        action = result["_id"]["action_type"]
        count = result["count"]
        
        if date not in trends:
            trends[date] = {"date": date, "impression": 0, "click": 0, "view": 0}
        
        trends[date][action] = count
    
    # 计算CTR
    for date, data in trends.items():
        if data["impression"] > 0:
            data["ctr"] = round(data["click"] / data["impression"], 4)
        else:
            data["ctr"] = 0
    
    return {
        "trends": list(trends.values()),
        "period_days": days
    }


@router.get("/items/distribution")
async def get_items_distribution(
    scenario_id: str,
    db=Depends(get_mongodb),
    context=Depends(get_tenant_user_context)
):
    """获取物品分布统计"""
    tenant_id = context["tenant_id"]
    
    # 按分类统计
    pipeline = [
        {"$match": {"tenant_id": tenant_id, "scenario_id": scenario_id}},
        {"$group": {
            "_id": "$metadata.category",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    
    category_stats = await db.items.aggregate(pipeline).to_list(length=None)
    
    # 按作者统计
    pipeline[1]["$group"]["_id"] = "$metadata.author"
    author_stats = await db.items.aggregate(pipeline).to_list(length=None)
    
    return {
        "category_distribution": [
            {"category": stat["_id"], "count": stat["count"]}
            for stat in category_stats
        ],
        "top_authors": [
            {"author": stat["_id"], "count": stat["count"]}
            for stat in author_stats
        ]
    }


@router.get("/users/behavior-analysis")
async def get_user_behavior_analysis(
    scenario_id: str,
    days: int = Query(7, ge=1, le=90),
    db=Depends(get_mongodb),
    context=Depends(get_tenant_user_context)
):
    """用户行为分析"""
    tenant_id = context["tenant_id"]
    start_time = datetime.utcnow() - timedelta(days=days)
    
    # 活跃时段分布
    pipeline = [
        {
            "$match": {
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "timestamp": {"$gte": start_time}
            }
        },
        {
            "$group": {
                "_id": {"$hour": "$timestamp"},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    hour_distribution = await db.interactions.aggregate(pipeline).to_list(length=None)
    
    # 用户活跃度分布（按行为数分段）
    user_activity_pipeline = [
        {
            "$match": {
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "timestamp": {"$gte": start_time}
            }
        },
        {
            "$group": {
                "_id": "$user_id",
                "action_count": {"$sum": 1}
            }
        },
        {
            "$bucket": {
                "groupBy": "$action_count",
                "boundaries": [0, 5, 20, 50, 100, 500],
                "default": "500+",
                "output": {"count": {"$sum": 1}}
            }
        }
    ]
    
    activity_distribution = await db.interactions.aggregate(
        user_activity_pipeline
    ).to_list(length=None)
    
    return {
        "hour_distribution": [
            {"hour": stat["_id"], "count": stat["count"]}
            for stat in hour_distribution
        ],
        "activity_distribution": activity_distribution
    }


@router.post("/data/export")
async def export_data(
    data_type: str = Query(..., regex="^(interactions|items|user_profiles)$"),
    scenario_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db=Depends(get_mongodb),
    context=Depends(get_tenant_user_context)
):
    """
    数据导出
    
    Args:
        data_type: 数据类型（interactions/items/user_profiles）
        scenario_id: 场景ID（可选）
        start_date: 开始日期（YYYY-MM-DD）
        end_date: 结束日期（YYYY-MM-DD）
    """
    tenant_id = context["tenant_id"]
    
    # 构建查询
    query = {"tenant_id": tenant_id}
    if scenario_id:
        query["scenario_id"] = scenario_id
    
    if start_date and end_date:
        query["timestamp"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    # 获取集合
    collection = getattr(db, data_type)
    
    # 导出数据（限制10000条）
    data = await collection.find(query).limit(10000).to_list(length=10000)
    
    # 清理MongoDB的_id字段
    for item in data:
        if "_id" in item:
            del item["_id"]
        # 转换datetime为ISO字符串
        for key, value in item.items():
            if isinstance(value, datetime):
                item[key] = value.isoformat()
    
    return {
        "data_type": data_type,
        "count": len(data),
        "data": data[:100],  # 只返回前100条预览
        "message": f"导出 {len(data)} 条数据"
    }


@router.get("/system/health")
async def system_health_check(
    db=Depends(get_mongodb)
):
    """系统健康检查"""
    health = {
        "status": "healthy",
        "checks": {}
    }
    
    # MongoDB连接检查
    try:
        await db.command("ping")
        health["checks"]["mongodb"] = "ok"
    except Exception as e:
        health["checks"]["mongodb"] = f"error: {str(e)}"
        health["status"] = "unhealthy"
    
    # Redis连接检查
    try:
        redis_client = get_redis()
        if redis_client:
            await redis_client.ping()
            health["checks"]["redis"] = "ok"
        else:
            health["checks"]["redis"] = "not_configured"
    except Exception as e:
        health["checks"]["redis"] = f"error: {str(e)}"
        health["status"] = "unhealthy"
    
    # Kafka连接检查（尝试连接）
    try:
        from app.core.kafka import KafkaProducer
        producer = KafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
        if producer.producer:
            health["checks"]["kafka"] = "configured"
        else:
            health["checks"]["kafka"] = "simulated_mode"
    except Exception as e:
        health["checks"]["kafka"] = f"error: {str(e)}"
        # Kafka不是关键依赖，不设置unhealthy
    
    return health


@router.get("/experiments/summary")
async def get_experiments_summary(
    db=Depends(get_mongodb),
    context=Depends(get_tenant_user_context)
):
    """实验汇总"""
    tenant_id = context["tenant_id"]
    
    # 统计各状态的实验数
    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]
    
    status_stats = await db.experiments.aggregate(pipeline).to_list(length=None)
    
    # 获取最近5个实验
    recent_experiments = await db.experiments.find(
        {"tenant_id": tenant_id}
    ).sort("created_at", -1).limit(5).to_list(length=5)
    
    return {
        "status_distribution": {
            stat["_id"]: stat["count"]
            for stat in status_stats
        },
        "recent_experiments": [
            {
                "experiment_id": exp["experiment_id"],
                "name": exp["name"],
                "status": exp["status"],
                "created_at": exp["created_at"].isoformat()
            }
            for exp in recent_experiments
        ]
    }

