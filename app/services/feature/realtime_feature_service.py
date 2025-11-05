"""
实时特征服务

提供实时特征查询，用于模型推理
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase


class RealtimeFeatureService:
    """
    实时特征服务
    
    功能:
    1. 用户实时特征查询
    2. 物品实时特征查询
    3. 交叉特征计算
    4. 特征缓存
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, redis_client=None):
        self.db = db
        self.redis = redis_client
        
        # 特征TTL配置
        self.ttl_config = {
            "user_realtime": 300,      # 5分钟
            "item_realtime": 600,      # 10分钟
            "cross_features": 60       # 1分钟
        }
    
    # ==================== 用户实时特征 ====================
    
    async def get_user_realtime_features(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        获取用户实时特征
        
        特征包括:
        - 最近1小时浏览次数
        - 最近1小时点击次数
        - 最近活跃时间
        - 活跃时长
        - 当前会话行为序列
        """
        # 尝试从缓存获取
        cached = await self._get_cached_user_features(tenant_id, scenario_id, user_id)
        if cached:
            return cached
        
        # 实时计算
        features = await self._compute_user_realtime_features(
            tenant_id, scenario_id, user_id
        )
        
        # 写入缓存
        await self._cache_user_features(
            tenant_id, scenario_id, user_id, features
        )
        
        return features
    
    async def _compute_user_realtime_features(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """计算用户实时特征"""
        
        # 1. 从Redis获取用户最近1小时行为
        behavior_key = f"user:behaviors:recent:{tenant_id}:{scenario_id}:{user_id}"
        
        features = {
            "view_count_1h": 0,
            "click_count_1h": 0,
            "last_active_time": None,
            "active_duration_seconds": 0,
            "behavior_sequence": []
        }
        
        try:
            if self.redis:
                # 获取最近行为列表（ZSET，按时间戳排序）
                now_ts = datetime.utcnow().timestamp()
                one_hour_ago_ts = (datetime.utcnow() - timedelta(hours=1)).timestamp()
                
                # 获取最近1小时的行为
                recent_behaviors = await self.redis.zrangebyscore(
                    behavior_key,
                    one_hour_ago_ts,
                    now_ts,
                    withscores=True
                )
                
                if recent_behaviors:
                    for behavior_data, timestamp in recent_behaviors:
                        behavior = json.loads(behavior_data)
                        behavior_type = behavior.get("type")
                        
                        if behavior_type == "view":
                            features["view_count_1h"] += 1
                        elif behavior_type == "click":
                            features["click_count_1h"] += 1
                        
                        features["behavior_sequence"].append({
                            "type": behavior_type,
                            "item_id": behavior.get("item_id"),
                            "timestamp": timestamp
                        })
                    
                    # 最后活跃时间
                    features["last_active_time"] = recent_behaviors[-1][1]
                    
                    # 活跃时长（第一次到最后一次的时间差）
                    if len(recent_behaviors) > 1:
                        features["active_duration_seconds"] = int(
                            recent_behaviors[-1][1] - recent_behaviors[0][1]
                        )
        
        except Exception as e:
            print(f"[RealtimeFeature] 计算用户特征失败: {e}")
        
        return features
    
    async def _get_cached_user_features(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """从缓存获取用户特征"""
        key = f"feature:user_realtime:{tenant_id}:{scenario_id}:{user_id}"
        
        try:
            if self.redis:
                cached = await self.redis.get(key)
                if cached:
                    return json.loads(cached)
        except Exception as e:
            print(f"[RealtimeFeature] 获取用户特征缓存失败: {e}")
        
        return None
    
    async def _cache_user_features(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        features: Dict[str, Any]
    ):
        """缓存用户特征"""
        key = f"feature:user_realtime:{tenant_id}:{scenario_id}:{user_id}"
        ttl = self.ttl_config["user_realtime"]
        
        try:
            if self.redis:
                await self.redis.setex(key, ttl, json.dumps(features))
        except Exception as e:
            print(f"[RealtimeFeature] 缓存用户特征失败: {e}")
    
    # ==================== 物品实时特征 ====================
    
    async def get_item_realtime_features(
        self,
        tenant_id: str,
        scenario_id: str,
        item_id: str
    ) -> Dict[str, Any]:
        """
        获取物品实时特征
        
        特征包括:
        - 最近1小时曝光量
        - 最近1小时点击量
        - 最近1小时CTR
        - 实时热度分
        """
        # 尝试从缓存获取
        cached = await self._get_cached_item_features(tenant_id, scenario_id, item_id)
        if cached:
            return cached
        
        # 实时计算
        features = await self._compute_item_realtime_features(
            tenant_id, scenario_id, item_id
        )
        
        # 写入缓存
        await self._cache_item_features(
            tenant_id, scenario_id, item_id, features
        )
        
        return features
    
    async def _compute_item_realtime_features(
        self,
        tenant_id: str,
        scenario_id: str,
        item_id: str
    ) -> Dict[str, Any]:
        """计算物品实时特征"""
        
        features = {
            "impression_count_1h": 0,
            "click_count_1h": 0,
            "ctr_1h": 0.0,
            "hot_score": 0.0
        }
        
        try:
            if self.redis:
                # 从Redis ZSET获取物品热度
                hot_key = f"hot:items:{scenario_id}"
                score = await self.redis.zscore(hot_key, item_id)
                if score:
                    features["hot_score"] = float(score)
                
                # 获取最近1小时的统计
                stats_key = f"item:stats:1h:{tenant_id}:{scenario_id}:{item_id}"
                stats = await self.redis.hgetall(stats_key)
                
                if stats:
                    impression_key = b"impression_count" if isinstance(list(stats.keys())[0], bytes) else "impression_count"
                    click_key = b"click_count" if isinstance(list(stats.keys())[0], bytes) else "click_count"
                    
                    impression_count = int(stats.get(impression_key, 0))
                    click_count = int(stats.get(click_key, 0))
                    
                    features["impression_count_1h"] = impression_count
                    features["click_count_1h"] = click_count
                    
                    # 计算CTR
                    if impression_count > 0:
                        features["ctr_1h"] = click_count / impression_count
        
        except Exception as e:
            print(f"[RealtimeFeature] 计算物品特征失败: {e}")
        
        return features
    
    async def _get_cached_item_features(
        self,
        tenant_id: str,
        scenario_id: str,
        item_id: str
    ) -> Optional[Dict[str, Any]]:
        """从缓存获取物品特征"""
        key = f"feature:item_realtime:{tenant_id}:{scenario_id}:{item_id}"
        
        try:
            if self.redis:
                cached = await self.redis.get(key)
                if cached:
                    return json.loads(cached)
        except Exception as e:
            print(f"[RealtimeFeature] 获取物品特征缓存失败: {e}")
        
        return None
    
    async def _cache_item_features(
        self,
        tenant_id: str,
        scenario_id: str,
        item_id: str,
        features: Dict[str, Any]
    ):
        """缓存物品特征"""
        key = f"feature:item_realtime:{tenant_id}:{scenario_id}:{item_id}"
        ttl = self.ttl_config["item_realtime"]
        
        try:
            if self.redis:
                await self.redis.setex(key, ttl, json.dumps(features))
        except Exception as e:
            print(f"[RealtimeFeature] 缓存物品特征失败: {e}")
    
    # ==================== 交叉特征 ====================
    
    async def get_cross_features(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        item_id: str
    ) -> Dict[str, Any]:
        """
        获取交叉特征
        
        特征包括:
        - 用户是否浏览过该物品
        - 用户最后一次浏览该物品的时间
        - 用户对该物品的兴趣度
        """
        features = {
            "user_viewed_item": False,
            "last_view_timestamp": None,
            "user_item_affinity": 0.0
        }
        
        try:
            # 从用户画像查询
            profile = await self.db.user_profiles.find_one({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "user_id": user_id
            })
            
            if profile:
                # 检查是否浏览过
                viewed_items = profile.get("preferences", {}).get("viewed_items", [])
                if item_id in viewed_items:
                    features["user_viewed_item"] = True
                
                # 兴趣度（基于标签匹配）
                user_tags = profile.get("tags", [])
                if user_tags:
                    # 获取物品信息
                    item = await self.db.items.find_one({
                        "tenant_id": tenant_id,
                        "scenario_id": scenario_id,
                        "item_id": item_id
                    })
                    
                    if item:
                        item_tags = item.get("metadata", {}).get("tags", [])
                        if item_tags:
                            # 计算标签匹配度
                            common_tags = set(user_tags) & set(item_tags)
                            features["user_item_affinity"] = len(common_tags) / len(set(user_tags) | set(item_tags))
        
        except Exception as e:
            print(f"[RealtimeFeature] 计算交叉特征失败: {e}")
        
        return features
    
    # ==================== 批量查询 ====================
    
    async def batch_get_item_features(
        self,
        tenant_id: str,
        scenario_id: str,
        item_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """批量获取物品特征"""
        results = {}
        
        for item_id in item_ids:
            features = await self.get_item_realtime_features(
                tenant_id, scenario_id, item_id
            )
            results[item_id] = features
        
        return results
    
    # ==================== 特征更新 ====================
    
    async def update_user_behavior(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        behavior_type: str,
        item_id: str = None
    ):
        """更新用户行为（用于实时特征计算）"""
        behavior_key = f"user:behaviors:recent:{tenant_id}:{scenario_id}:{user_id}"
        
        try:
            if self.redis:
                # 添加到ZSET（score为时间戳）
                behavior_data = json.dumps({
                    "type": behavior_type,
                    "item_id": item_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                timestamp = datetime.utcnow().timestamp()
                await self.redis.zadd(behavior_key, {behavior_data: timestamp})
                
                # 只保留最近1小时的数据
                one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).timestamp()
                await self.redis.zremrangebyscore(behavior_key, 0, one_hour_ago)
                
                # 设置过期时间（2小时）
                await self.redis.expire(behavior_key, 7200)
        
        except Exception as e:
            print(f"[RealtimeFeature] 更新用户行为失败: {e}")
    
    async def update_item_stats(
        self,
        tenant_id: str,
        scenario_id: str,
        item_id: str,
        event_type: str
    ):
        """更新物品统计（曝光/点击）"""
        stats_key = f"item:stats:1h:{tenant_id}:{scenario_id}:{item_id}"
        
        try:
            if self.redis:
                if event_type == "impression":
                    await self.redis.hincrby(stats_key, "impression_count", 1)
                elif event_type == "click":
                    await self.redis.hincrby(stats_key, "click_count", 1)
                
                # 设置过期时间（2小时）
                await self.redis.expire(stats_key, 7200)
        
        except Exception as e:
            print(f"[RealtimeFeature] 更新物品统计失败: {e}")

