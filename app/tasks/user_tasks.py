"""
用户相关的离线任务
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.tasks.celery_app import celery_app
from app.core.database import get_database
from app.core.redis_client import get_redis_client


@celery_app.task(name="app.tasks.user_tasks.update_user_profiles_batch", bind=True)
def update_user_profiles_batch(self):
    """
    批量更新用户画像（离线聚合）
    
    功能:
    - 统计用户历史行为
    - 计算用户偏好
    - 更新用户活跃度
    - 写入MongoDB和Redis缓存
    """
    print("=" * 60)
    print(f"  离线任务: 批量更新用户画像")
    print(f"  任务ID: {self.request.id}")
    print("=" * 60)
    
    db = get_database()
    redis = get_redis_client()
    
    # 获取所有场景
    scenarios = list(db.scenarios.find({}))
    
    total_users = 0
    
    for scenario in scenarios:
        tenant_id = scenario["tenant_id"]
        scenario_id = scenario["scenario_id"]
        
        print(f"\n处理场景: {tenant_id}/{scenario_id}")
        
        # 1. 获取活跃用户（最近30天有交互）
        start_time = datetime.utcnow() - timedelta(days=30)
        
        active_users = db.interactions.distinct(
            "user_id",
            {
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "timestamp": {"$gte": start_time}
            }
        )
        
        print(f"  活跃用户数: {len(active_users)}")
        
        # 2. 为每个用户更新画像
        for user_id in active_users:
            try:
                profile = _compute_user_profile(
                    db, tenant_id, scenario_id, user_id
                )
                
                # 3. 更新MongoDB
                db.user_profiles.update_one(
                    {
                        "tenant_id": tenant_id,
                        "scenario_id": scenario_id,
                        "user_id": user_id
                    },
                    {"$set": profile},
                    upsert=True
                )
                
                # 4. 更新Redis缓存
                redis_key = f"user:profile:{tenant_id}:{user_id}:{scenario_id}"
                redis.setex(
                    redis_key,
                    3600 * 24 * 7,  # 7天过期
                    str(profile)  # 简化，实际应序列化为JSON
                )
                
                total_users += 1
                
            except Exception as e:
                print(f"  用户 {user_id} 更新失败: {e}")
                continue
        
        print(f"  完成: {len(active_users)} 个用户")
    
    print()
    print("=" * 60)
    print(f"  任务完成")
    print(f"  更新用户数: {total_users}")
    print("=" * 60)
    
    return {
        "task_id": self.request.id,
        "updated_users": total_users,
        "scenarios": len(scenarios),
        "timestamp": datetime.utcnow().isoformat()
    }


def _compute_user_profile(
    db,
    tenant_id: str,
    scenario_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    计算单个用户的画像
    
    Returns:
        用户画像字典
    """
    # 1. 获取用户交互历史（最近30天）
    start_time = datetime.utcnow() - timedelta(days=30)
    
    interactions = list(db.interactions.find({
        "tenant_id": tenant_id,
        "scenario_id": scenario_id,
        "user_id": user_id,
        "timestamp": {"$gte": start_time}
    }).sort("timestamp", -1).limit(1000))
    
    # 2. 统计特征
    features = {
        "total_actions": len(interactions),
        "action_types": {},
        "categories": {},
        "authors": {},
        "active_days": set(),
        "active_hours": []
    }
    
    for inter in interactions:
        # 行为类型统计
        action = inter["action_type"]
        features["action_types"][action] = features["action_types"].get(action, 0) + 1
        
        # 活跃天数
        day = inter["timestamp"].date().isoformat()
        features["active_days"].add(day)
        
        # 活跃时段
        hour = inter["timestamp"].hour
        features["active_hours"].append(hour)
        
        # 获取物品元数据
        item = db.items.find_one({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "item_id": inter["item_id"]
        })
        
        if item:
            metadata = item.get("metadata", {})
            
            # 分类偏好
            category = metadata.get("category")
            if category:
                features["categories"][category] = \
                    features["categories"].get(category, 0) + 1
            
            # 作者偏好
            author = metadata.get("author")
            if author:
                features["authors"][author] = \
                    features["authors"].get(author, 0) + 1
    
    # 3. 计算偏好分数
    total_categories = sum(features["categories"].values())
    category_preferences = {
        cat: count / total_categories
        for cat, count in features["categories"].items()
    } if total_categories > 0 else {}
    
    total_authors = sum(features["authors"].values())
    author_preferences = {
        author: count / total_authors
        for author, count in features["authors"].items()
    } if total_authors > 0 else {}
    
    # 4. 活跃度分析
    active_day_count = len(features["active_days"])
    avg_actions_per_day = len(interactions) / max(active_day_count, 1)
    
    # 活跃时段分布
    hour_distribution = {}
    for hour in features["active_hours"]:
        hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
    
    # 5. 构建画像
    profile = {
        "tenant_id": tenant_id,
        "scenario_id": scenario_id,
        "user_id": user_id,
        "features": {
            "total_actions": features["total_actions"],
            "action_counts": features["action_types"],
            "active_days": active_day_count,
            "avg_actions_per_day": round(avg_actions_per_day, 2)
        },
        "preferences": {
            "categories": category_preferences,
            "authors": author_preferences
        },
        "activity": {
            "hour_distribution": hour_distribution,
            "most_active_hours": sorted(
                hour_distribution.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3] if hour_distribution else []
        },
        "updated_at": datetime.utcnow()
    }
    
    return profile


@celery_app.task(name="app.tasks.user_tasks.compute_user_embeddings")
def compute_user_embeddings(tenant_id: str, scenario_id: str, user_ids: List[str] = None):
    """
    计算用户向量（基于历史交互）
    
    Args:
        tenant_id: 租户ID
        scenario_id: 场景ID
        user_ids: 用户ID列表（可选）
    """
    print(f"[Task] 计算用户向量: {tenant_id}/{scenario_id}")
    
    db = get_database()
    
    # TODO: 实际Milvus集成后实现
    # 1. 获取用户交互历史
    # 2. 聚合物品向量（加权平均）
    # 3. 写入Milvus
    
    query = {"tenant_id": tenant_id, "scenario_id": scenario_id}
    if user_ids:
        query["user_id"] = {"$in": user_ids}
    
    users = list(db.user_profiles.find(query).limit(1000))
    
    print(f"  待计算用户数: {len(users)}")
    
    return {
        "tenant_id": tenant_id,
        "scenario_id": scenario_id,
        "computed_count": len(users)
    }


@celery_app.task(name="app.tasks.user_tasks.segment_users")
def segment_users(tenant_id: str, scenario_id: str):
    """
    用户分群（基于行为模式）
    
    分群维度:
    - 活跃度: 高活跃/中活跃/低活跃
    - 偏好: 不同内容分类偏好
    - 生命周期: 新用户/成长期/成熟期/流失期
    """
    print(f"[Task] 用户分群: {tenant_id}/{scenario_id}")
    
    db = get_database()
    
    # 获取所有用户画像
    profiles = list(db.user_profiles.find({
        "tenant_id": tenant_id,
        "scenario_id": scenario_id
    }))
    
    print(f"  用户总数: {len(profiles)}")
    
    # 按活跃度分群
    segments = {
        "high_active": [],
        "medium_active": [],
        "low_active": []
    }
    
    for profile in profiles:
        avg_actions = profile.get("features", {}).get("avg_actions_per_day", 0)
        
        if avg_actions >= 10:
            segments["high_active"].append(profile["user_id"])
        elif avg_actions >= 3:
            segments["medium_active"].append(profile["user_id"])
        else:
            segments["low_active"].append(profile["user_id"])
    
    print(f"  高活跃: {len(segments['high_active'])}")
    print(f"  中活跃: {len(segments['medium_active'])}")
    print(f"  低活跃: {len(segments['low_active'])}")
    
    # 存储分群结果
    db.user_segments.update_one(
        {"tenant_id": tenant_id, "scenario_id": scenario_id},
        {"$set": {
            "segments": segments,
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )
    
    return {
        "tenant_id": tenant_id,
        "scenario_id": scenario_id,
        "segments": {k: len(v) for k, v in segments.items()}
    }

