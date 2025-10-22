"""
物品相关的离线任务
"""
from typing import Dict, Any, List
from datetime import datetime
import numpy as np
from app.tasks.celery_app import celery_app
from app.core.database import get_database
from app.core.redis_client import get_redis_client


@celery_app.task(name="app.tasks.item_tasks.compute_item_similarity", bind=True)
def compute_item_similarity(self, tenant_id: str = None, scenario_id: str = None):
    """
    批量计算物品相似度（基于协同过滤）
    
    算法: Item-Based Collaborative Filtering
    - 相似度计算: Cosine Similarity
    - 存储: Redis ZSET
    
    Args:
        tenant_id: 租户ID（可选，不指定则处理所有租户）
        scenario_id: 场景ID（可选）
    """
    print("=" * 60)
    print(f"  离线任务: 计算物品相似度")
    print(f"  任务ID: {self.request.id}")
    print("=" * 60)
    
    db = get_database()
    redis = get_redis_client()
    
    # 获取所有需要处理的场景
    scenarios_query = {}
    if tenant_id:
        scenarios_query["tenant_id"] = tenant_id
    if scenario_id:
        scenarios_query["scenario_id"] = scenario_id
    
    scenarios = list(db.scenarios.find(scenarios_query))
    
    total_processed = 0
    
    for scenario in scenarios:
        tenant_id = scenario["tenant_id"]
        scenario_id = scenario["scenario_id"]
        
        print(f"\n处理场景: {tenant_id}/{scenario_id}")
        
        # 1. 获取用户-物品交互矩阵
        interactions = list(db.interactions.find({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "action_type": {"$in": ["view", "like", "favorite"]}
        }))
        
        if not interactions:
            print("  无交互数据，跳过")
            continue
        
        # 2. 构建共现矩阵
        # 物品 -> 用户列表
        item_users = {}
        for inter in interactions:
            item_id = inter["item_id"]
            user_id = inter["user_id"]
            
            if item_id not in item_users:
                item_users[item_id] = set()
            item_users[item_id].add(user_id)
        
        item_ids = list(item_users.keys())
        n = len(item_ids)
        
        print(f"  物品数量: {n}")
        print(f"  交互数量: {len(interactions)}")
        
        # 3. 计算物品相似度（Item-Item）
        similarity_pairs = []
        
        for i, item_i in enumerate(item_ids):
            users_i = item_users[item_i]
            similar_items = []
            
            for j, item_j in enumerate(item_ids):
                if i >= j:  # 避免重复计算
                    continue
                
                users_j = item_users[item_j]
                
                # Cosine相似度
                intersection = len(users_i & users_j)
                if intersection == 0:
                    continue
                
                similarity = intersection / np.sqrt(len(users_i) * len(users_j))
                
                if similarity > 0.1:  # 阈值过滤
                    similar_items.append((item_j, similarity))
            
            # 排序并保留Top 100
            similar_items.sort(key=lambda x: x[1], reverse=True)
            similar_items = similar_items[:100]
            
            # 存储到Redis
            if similar_items:
                redis_key = f"item:similar:{tenant_id}:{scenario_id}:{item_i}"
                redis.delete(redis_key)
                
                for similar_item_id, score in similar_items:
                    redis.zadd(redis_key, {similar_item_id: score})
                
                redis.expire(redis_key, 86400 * 7)  # 7天过期
                
                total_processed += 1
            
            if i % 100 == 0:
                print(f"  进度: {i}/{n}")
    
    print()
    print("=" * 60)
    print(f"  任务完成")
    print(f"  处理物品数: {total_processed}")
    print("=" * 60)
    
    return {
        "task_id": self.request.id,
        "processed_items": total_processed,
        "scenarios": len(scenarios),
        "timestamp": datetime.utcnow().isoformat()
    }


@celery_app.task(name="app.tasks.item_tasks.generate_item_embeddings")
def generate_item_embeddings(tenant_id: str, scenario_id: str, item_ids: List[str]):
    """
    生成物品向量并写入Milvus（用于向量召回）
    
    Args:
        tenant_id: 租户ID
        scenario_id: 场景ID
        item_ids: 物品ID列表
    """
    if not item_ids:
        return {"updated_count": 0}
    
    print(f"[Task] 生成物品向量: {tenant_id}/{scenario_id}, 数量: {len(item_ids)}")
    
    from app.core.database import get_database
    from app.core.milvus_client import MilvusClient, MilvusCollections, EmbeddingGenerator
    from app.core.config import settings
    
    db = get_database()
    
    # 1. 从MongoDB读取物品元数据
    items = list(db.items.find({
        "tenant_id": tenant_id,
        "scenario_id": scenario_id,
        "item_id": {"$in": item_ids}
    }))
    
    if not items:
        print(f"  未找到物品数据")
        return {"updated_count": 0}
    
    print(f"  查询到物品数: {len(items)}")
    
    # 2. 初始化Milvus客户端
    milvus_client = MilvusClient(
        host=settings.milvus_host,
        port=settings.milvus_port,
        enabled=settings.milvus_enabled
    )
    
    if not milvus_client.enabled:
        print(f"  Milvus未启用，跳过向量生成")
        return {"updated_count": 0, "milvus_enabled": False}
    
    # 3. 获取场景类型（确定collection名称）
    scenario = db.scenarios.find_one({
        "tenant_id": tenant_id,
        "scenario_id": scenario_id
    })
    
    scenario_type = scenario.get("scenario_type", "default") if scenario else "default"
    collection_name = MilvusCollections.items_embeddings(scenario_type)
    
    # 4. 生成向量
    item_ids_for_milvus = []
    embeddings = []
    
    for item in items:
        try:
            # 使用EmbeddingGenerator生成向量
            embedding = EmbeddingGenerator.generate_item_embedding(item.get("metadata", {}))
            
            item_ids_for_milvus.append(item["item_id"])
            embeddings.append(embedding)
            
        except Exception as e:
            print(f"  生成向量失败 {item['item_id']}: {e}")
            continue
    
    if not embeddings:
        print(f"  无向量生成")
        return {"updated_count": 0}
    
    print(f"  成功生成向量数: {len(embeddings)}")
    
    # 5. 写入Milvus
    try:
        # 确保collection存在
        import asyncio
        asyncio.run(milvus_client.create_collection(
            collection_name=collection_name,
            dimension=768,
            description=f"Items embeddings for {scenario_type}"
        ))
        
        # 批量插入向量
        inserted_count = asyncio.run(milvus_client.insert_vectors(
            collection_name=collection_name,
            tenant_id=tenant_id,
            scenario_id=scenario_id,
            item_ids=item_ids_for_milvus,
            embeddings=embeddings
        ))
        
        print(f"  ✅ 写入Milvus成功: {inserted_count}个向量")
        
        # 6. 更新MongoDB中的embedding字段（可选，用于调试）
        for item_id, embedding in zip(item_ids_for_milvus, embeddings):
            db.items.update_one(
                {"tenant_id": tenant_id, "scenario_id": scenario_id, "item_id": item_id},
                {"$set": {"embedding": embedding[:10], "embedding_updated_at": datetime.utcnow()}}  # 只存前10维用于展示
            )
        
        return {
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "collection_name": collection_name,
            "updated_count": inserted_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"  ❌ 写入Milvus失败: {e}")
        return {
            "updated_count": 0,
            "error": str(e)
        }


@celery_app.task(name="app.tasks.item_tasks.update_item_embeddings")
def update_item_embeddings(tenant_id: str, scenario_id: str, item_ids: List[str] = None):
    """
    批量更新物品向量（定时任务用）
    
    Args:
        tenant_id: 租户ID
        scenario_id: 场景ID
        item_ids: 物品ID列表（可选，不指定则更新所有）
    """
    print(f"[Task] 批量更新物品向量: {tenant_id}/{scenario_id}")
    
    db = get_database()
    
    # 查询物品
    query = {"tenant_id": tenant_id, "scenario_id": scenario_id}
    if item_ids:
        query["item_id"] = {"$in": item_ids}
    
    items = list(db.items.find(query).limit(1000))
    
    if not items:
        print(f"  未找到物品")
        return {"updated_count": 0}
    
    item_ids_to_update = [item["item_id"] for item in items]
    
    # 调用generate_item_embeddings处理
    return generate_item_embeddings(tenant_id, scenario_id, item_ids_to_update)


@celery_app.task(name="app.tasks.item_tasks.cleanup_inactive_items")
def cleanup_inactive_items(days: int = 90):
    """
    清理不活跃物品（超过N天无交互）
    
    Args:
        days: 天数阈值
    """
    print(f"[Task] 清理不活跃物品: >{days}天无交互")
    
    db = get_database()
    redis = get_redis_client()
    
    # TODO: 实现清理逻辑
    # 1. 查找超过N天无交互的物品
    # 2. 标记为inactive
    # 3. 清理相关缓存
    
    return {
        "cleaned_count": 0,
        "threshold_days": days
    }

