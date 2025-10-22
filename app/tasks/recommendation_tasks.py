"""
推荐相关的离线任务
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.tasks.celery_app import celery_app
from app.core.database import get_database
from app.core.redis_client import get_redis_client


@celery_app.task(name="app.tasks.recommendation_tasks.precompute_recommendations", bind=True)
def precompute_recommendations(self, tenant_id: str = None, scenario_id: str = None):
    """
    预计算推荐结果（离线批量生成）
    
    适用场景:
    - 对高活跃用户预计算Top N推荐
    - 减少在线计算压力
    - 提升首屏加载速度
    
    流程:
    1. 识别高活跃用户
    2. 批量召回候选集
    3. 批量排序打分
    4. 缓存到Redis
    """
    print("=" * 60)
    print(f"  离线任务: 预计算推荐结果")
    print(f"  任务ID: {self.request.id}")
    print("=" * 60)
    
    db = get_database()
    redis = get_redis_client()
    
    # 获取场景
    scenarios_query = {}
    if tenant_id:
        scenarios_query["tenant_id"] = tenant_id
    if scenario_id:
        scenarios_query["scenario_id"] = scenario_id
    
    scenarios = list(db.scenarios.find(scenarios_query))
    
    total_users = 0
    
    for scenario in scenarios:
        tenant_id = scenario["tenant_id"]
        scenario_id = scenario["scenario_id"]
        
        print(f"\n处理场景: {tenant_id}/{scenario_id}")
        
        # 1. 获取高活跃用户（最近7天日活>=3次）
        start_time = datetime.utcnow() - timedelta(days=7)
        
        # 聚合统计每日活跃度
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
                    "_id": {
                        "user_id": "$user_id",
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$group": {
                    "_id": "$_id.user_id",
                    "active_days": {"$sum": 1},
                    "total_actions": {"$sum": "$count"}
                }
            },
            {
                "$match": {
                    "active_days": {"$gte": 3}
                }
            }
        ]
        
        active_users = list(db.interactions.aggregate(pipeline))
        
        print(f"  高活跃用户数: {len(active_users)}")
        
        # 2. 为每个高活跃用户预计算推荐
        for user_stat in active_users[:1000]:  # 限制处理数量
            user_id = user_stat["_id"]
            
            try:
                # 生成推荐列表
                recommendations = _generate_recommendations(
                    db, redis, tenant_id, scenario_id, user_id
                )
                
                if not recommendations:
                    continue
                
                # 3. 缓存到Redis
                redis_key = f"rec:precomputed:{tenant_id}:{user_id}:{scenario_id}"
                
                # 使用ZSET存储（score为推荐分数）
                redis.delete(redis_key)
                for idx, item_id in enumerate(recommendations):
                    score = len(recommendations) - idx  # 简化的分数
                    redis.zadd(redis_key, {item_id: score})
                
                # 设置过期时间（4小时）
                redis.expire(redis_key, 3600 * 4)
                
                total_users += 1
                
            except Exception as e:
                print(f"  用户 {user_id} 预计算失败: {e}")
                continue
        
        print(f"  完成: {min(len(active_users), 1000)} 个用户")
    
    print()
    print("=" * 60)
    print(f"  任务完成")
    print(f"  预计算用户数: {total_users}")
    print("=" * 60)
    
    return {
        "task_id": self.request.id,
        "precomputed_users": total_users,
        "scenarios": len(scenarios),
        "timestamp": datetime.utcnow().isoformat()
    }


def _generate_recommendations(
    db,
    redis,
    tenant_id: str,
    scenario_id: str,
    user_id: str,
    top_n: int = 100
) -> List[str]:
    """
    生成推荐列表（简化版）
    
    Returns:
        推荐物品ID列表
    """
    # 1. 获取用户最近交互的物品
    recent_items = list(db.interactions.find({
        "tenant_id": tenant_id,
        "scenario_id": scenario_id,
        "user_id": user_id,
        "action_type": {"$in": ["view", "like"]}
    }).sort("timestamp", -1).limit(10))
    
    recent_item_ids = {inter["item_id"] for inter in recent_items}
    
    # 2. 基于物品相似度召回
    candidate_items = set()
    
    for item_id in list(recent_item_ids)[:5]:  # 只用最近5个物品
        # 从Redis获取相似物品
        redis_key = f"item:similar:{tenant_id}:{scenario_id}:{item_id}"
        similar_items = redis.zrevrange(redis_key, 0, 19)  # Top 20
        
        for similar_item in similar_items:
            if isinstance(similar_item, bytes):
                similar_item = similar_item.decode('utf-8')
            candidate_items.add(similar_item)
    
    # 3. 过滤已交互物品
    candidate_items -= recent_item_ids
    
    # 4. 获取热门物品作为补充
    hot_items_key = f"hot:items:{tenant_id}:{scenario_id}"
    hot_items = redis.zrevrange(hot_items_key, 0, 49)  # Top 50
    
    for hot_item in hot_items:
        if isinstance(hot_item, bytes):
            hot_item = hot_item.decode('utf-8')
        if hot_item not in recent_item_ids:
            candidate_items.add(hot_item)
    
    # 5. 返回Top N
    return list(candidate_items)[:top_n]


@celery_app.task(name="app.tasks.recommendation_tasks.cleanup_expired_cache")
def cleanup_expired_cache():
    """
    清理过期的推荐缓存
    
    功能:
    - 清理超过7天的推荐结果缓存
    - 清理无效的用户画像缓存
    - 释放Redis内存
    """
    print("[Task] 清理过期缓存")
    
    redis = get_redis_client()
    
    # TODO: 实现缓存清理逻辑
    # 1. 扫描特定前缀的key
    # 2. 检查过期时间
    # 3. 删除过期key
    
    # Redis会自动清理带TTL的key，这里可以做额外清理
    
    cleaned_count = 0
    
    # 示例：清理rec:precomputed:*前缀的过期key
    # cursor = 0
    # while True:
    #     cursor, keys = redis.scan(cursor, match="rec:precomputed:*", count=100)
    #     for key in keys:
    #         ttl = redis.ttl(key)
    #         if ttl == -1:  # 没有设置过期时间
    #             redis.expire(key, 3600 * 4)  # 设置4小时过期
    #     if cursor == 0:
    #         break
    
    return {
        "cleaned_keys": cleaned_count,
        "timestamp": datetime.utcnow().isoformat()
    }


@celery_app.task(name="app.tasks.recommendation_tasks.update_hot_items_cache")
def update_hot_items_cache(tenant_id: str, scenario_id: str):
    """
    更新热门物品缓存
    
    计算规则:
    - 最近24小时内的曝光、点击、点赞等行为
    - 时间衰减加权
    - Top 1000
    """
    print(f"[Task] 更新热门物品缓存: {tenant_id}/{scenario_id}")
    
    db = get_database()
    redis = get_redis_client()
    
    # 获取最近24小时的交互
    start_time = datetime.utcnow() - timedelta(hours=24)
    
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
                "_id": "$item_id",
                "impression_count": {
                    "$sum": {"$cond": [{"$eq": ["$action_type", "impression"]}, 1, 0]}
                },
                "view_count": {
                    "$sum": {"$cond": [{"$eq": ["$action_type", "view"]}, 1, 0]}
                },
                "like_count": {
                    "$sum": {"$cond": [{"$eq": ["$action_type", "like"]}, 1, 0]}
                }
            }
        }
    ]
    
    stats = list(db.interactions.aggregate(pipeline))
    
    # 计算热度分数
    hot_scores = {}
    for stat in stats:
        item_id = stat["_id"]
        score = (
            stat["impression_count"] * 0.5 +
            stat["view_count"] * 1.0 +
            stat["like_count"] * 3.0
        )
        hot_scores[item_id] = score
    
    # 写入Redis ZSET
    redis_key = f"hot:items:{tenant_id}:{scenario_id}"
    redis.delete(redis_key)
    
    if hot_scores:
        redis.zadd(redis_key, hot_scores)
    
    redis.expire(redis_key, 3600 * 2)  # 2小时过期
    
    print(f"  更新热门物品数: {len(hot_scores)}")
    
    return {
        "tenant_id": tenant_id,
        "scenario_id": scenario_id,
        "hot_items_count": len(hot_scores)
    }


@celery_app.task(name="app.tasks.recommendation_tasks.compute_recommendation_metrics")
def compute_recommendation_metrics(tenant_id: str, scenario_id: str, date: str = None):
    """
    计算推荐效果指标（离线分析）
    
    指标:
    - CTR（点击率）
    - 平均观看时长
    - 互动率
    - 新颖性
    - 多样性
    - 覆盖率
    
    Args:
        tenant_id: 租户ID
        scenario_id: 场景ID
        date: 日期（YYYY-MM-DD），默认为昨天
    """
    if date is None:
        date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"[Task] 计算推荐指标: {tenant_id}/{scenario_id}, 日期: {date}")
    
    db = get_database()
    
    # 获取指定日期的交互数据
    start_time = datetime.fromisoformat(f"{date}T00:00:00")
    end_time = datetime.fromisoformat(f"{date}T23:59:59")
    
    interactions = list(db.interactions.find({
        "tenant_id": tenant_id,
        "scenario_id": scenario_id,
        "timestamp": {"$gte": start_time, "$lte": end_time}
    }))
    
    # 统计指标
    impression_count = sum(1 for i in interactions if i["action_type"] == "impression")
    click_count = sum(1 for i in interactions if i["action_type"] == "click")
    view_count = sum(1 for i in interactions if i["action_type"] == "view")
    like_count = sum(1 for i in interactions if i["action_type"] == "like")
    
    ctr = click_count / impression_count if impression_count > 0 else 0
    engagement_rate = (like_count + view_count) / impression_count if impression_count > 0 else 0
    
    # 覆盖率：推荐物品占总物品的比例
    total_items = db.items.count_documents({
        "tenant_id": tenant_id,
        "scenario_id": scenario_id
    })
    recommended_items = len(set(i["item_id"] for i in interactions))
    coverage = recommended_items / total_items if total_items > 0 else 0
    
    metrics = {
        "tenant_id": tenant_id,
        "scenario_id": scenario_id,
        "date": date,
        "impression_count": impression_count,
        "click_count": click_count,
        "view_count": view_count,
        "like_count": like_count,
        "ctr": round(ctr, 4),
        "engagement_rate": round(engagement_rate, 4),
        "coverage": round(coverage, 4),
        "computed_at": datetime.utcnow().isoformat()
    }
    
    # 存储到MongoDB
    db.recommendation_metrics.update_one(
        {
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "date": date
        },
        {"$set": metrics},
        upsert=True
    )
    
    print(f"  CTR: {ctr:.4f}")
    print(f"  互动率: {engagement_rate:.4f}")
    print(f"  覆盖率: {coverage:.4f}")
    
    return metrics

