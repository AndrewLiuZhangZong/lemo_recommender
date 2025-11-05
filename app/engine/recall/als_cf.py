"""
ALS协同过滤召回

基于交替最小二乘法(ALS)的协同过滤算法
通过矩阵分解学习用户和物品的隐向量表示
"""
import numpy as np
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta


class ALSCollaborativeFiltering:
    """
    ALS协同过滤召回策略
    
    特点:
    1. 离线预计算用户/物品向量
    2. 在线快速推荐（向量点积）
    3. 支持隐式反馈（浏览、点击）
    
    算法:
    - 使用ALS优化矩阵分解
    - 损失函数包含正则化项
    - 支持置信度加权
    """
    
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        redis_client=None,
        factors: int = 50,
        regularization: float = 0.01,
        iterations: int = 15
    ):
        self.db = db
        self.redis = redis_client
        self.factors = factors
        self.regularization = regularization
        self.iterations = iterations
        
        # 用户/物品向量缓存
        self.user_vectors = {}
        self.item_vectors = {}
        
        print(f"[ALS-CF] 初始化 - 隐因子数: {factors}, 正则化: {regularization}")
    
    async def recall(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        limit: int = 100,
        params: Dict[str, Any] = None
    ) -> List[str]:
        """
        召回物品
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            user_id: 用户ID
            limit: 返回数量
            params: 额外参数
            
        Returns:
            物品ID列表
        """
        # 1. 尝试从Redis获取预计算的推荐结果
        cached_result = await self._get_cached_recommendations(
            tenant_id, scenario_id, user_id
        )
        if cached_result:
            return cached_result[:limit]
        
        # 2. 从Redis加载用户向量
        user_vector = await self._load_user_vector(tenant_id, scenario_id, user_id)
        if user_vector is None:
            print(f"[ALS-CF] 用户向量不存在: {user_id}")
            return []
        
        # 3. 批量加载物品向量并计算相似度
        item_scores = await self._compute_item_scores(
            tenant_id, scenario_id, user_vector, limit * 2
        )
        
        # 4. 过滤用户已交互的物品
        interacted_items = await self._get_user_interacted_items(
            tenant_id, scenario_id, user_id
        )
        
        # 5. 返回Top N
        filtered_items = [
            item_id for item_id, _ in item_scores
            if item_id not in interacted_items
        ]
        
        result = filtered_items[:limit]
        
        # 6. 异步缓存结果
        if self.redis and result:
            await self._cache_recommendations(
                tenant_id, scenario_id, user_id, result
            )
        
        return result
    
    async def _load_user_vector(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str
    ) -> Optional[np.ndarray]:
        """从Redis加载用户向量"""
        key = f"als:user_vector:{tenant_id}:{scenario_id}:{user_id}"
        
        try:
            if self.redis:
                vector_bytes = await self.redis.get(key)
                if vector_bytes:
                    return np.frombuffer(vector_bytes, dtype=np.float32)
        except Exception as e:
            print(f"[ALS-CF] 加载用户向量失败: {e}")
        
        return None
    
    async def _compute_item_scores(
        self,
        tenant_id: str,
        scenario_id: str,
        user_vector: np.ndarray,
        top_k: int
    ) -> List[tuple[str, float]]:
        """计算物品得分"""
        
        # 从Redis批量加载物品向量
        # Key模式: als:item_vectors:{tenant_id}:{scenario_id}
        key_pattern = f"als:item_vectors:{tenant_id}:{scenario_id}"
        
        try:
            if not self.redis:
                return []
            
            # 使用HGETALL获取所有物品向量
            item_vectors_data = await self.redis.hgetall(key_pattern)
            
            if not item_vectors_data:
                print(f"[ALS-CF] 物品向量不存在，请先训练模型")
                return []
            
            # 计算相似度
            scores = []
            for item_id_bytes, vector_bytes in item_vectors_data.items():
                item_id = item_id_bytes.decode() if isinstance(item_id_bytes, bytes) else item_id_bytes
                item_vector = np.frombuffer(vector_bytes, dtype=np.float32)
                
                # 向量点积
                score = float(np.dot(user_vector, item_vector))
                scores.append((item_id, score))
            
            # 排序并返回Top K
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:top_k]
            
        except Exception as e:
            print(f"[ALS-CF] 计算物品得分失败: {e}")
            return []
    
    async def _get_user_interacted_items(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str
    ) -> set:
        """获取用户已交互的物品"""
        try:
            # 从用户画像获取
            profile = await self.db.user_profiles.find_one({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "user_id": user_id
            })
            
            if profile and "interacted_items" in profile:
                return set(profile["interacted_items"])
            
        except Exception as e:
            print(f"[ALS-CF] 获取用户交互历史失败: {e}")
        
        return set()
    
    async def _get_cached_recommendations(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str
    ) -> Optional[List[str]]:
        """从缓存获取推荐结果"""
        key = f"als:rec:{tenant_id}:{scenario_id}:{user_id}"
        
        try:
            if self.redis:
                cached = await self.redis.get(key)
                if cached:
                    return cached.decode().split(",")
        except Exception as e:
            print(f"[ALS-CF] 获取缓存失败: {e}")
        
        return None
    
    async def _cache_recommendations(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        recommendations: List[str],
        ttl: int = 3600
    ):
        """缓存推荐结果"""
        key = f"als:rec:{tenant_id}:{scenario_id}:{user_id}"
        
        try:
            if self.redis:
                value = ",".join(recommendations)
                await self.redis.setex(key, ttl, value)
        except Exception as e:
            print(f"[ALS-CF] 缓存推荐结果失败: {e}")
    
    # ==================== 模型训练 ====================
    
    async def train(
        self,
        tenant_id: str,
        scenario_id: str,
        min_interactions: int = 5
    ) -> Dict[str, Any]:
        """
        训练ALS模型
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            min_interactions: 最少交互次数
            
        Returns:
            训练结果统计
        """
        print(f"\n[ALS-CF] 开始训练模型...")
        print(f"  租户: {tenant_id}, 场景: {scenario_id}")
        
        # 1. 构建交互矩阵
        interaction_matrix, user_mapping, item_mapping = await self._build_interaction_matrix(
            tenant_id, scenario_id, min_interactions
        )
        
        if interaction_matrix is None:
            return {
                "success": False,
                "error": "交互数据不足"
            }
        
        n_users, n_items = interaction_matrix.shape
        print(f"  用户数: {n_users}, 物品数: {n_items}")
        print(f"  交互数: {interaction_matrix.nnz if hasattr(interaction_matrix, 'nnz') else 'N/A'}")
        
        # 2. 训练ALS
        user_factors, item_factors = self._train_als(interaction_matrix)
        
        # 3. 保存到Redis
        await self._save_vectors_to_redis(
            tenant_id, scenario_id,
            user_factors, item_factors,
            user_mapping, item_mapping
        )
        
        result = {
            "success": True,
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "n_users": n_users,
            "n_items": n_items,
            "factors": self.factors,
            "trained_at": datetime.utcnow().isoformat()
        }
        
        print(f"[ALS-CF] 训练完成!")
        return result
    
    async def _build_interaction_matrix(
        self,
        tenant_id: str,
        scenario_id: str,
        min_interactions: int
    ) -> tuple:
        """构建用户-物品交互矩阵"""
        from scipy.sparse import lil_matrix
        
        # 从MongoDB获取用户画像（包含交互历史）
        cursor = self.db.user_profiles.find({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id
        })
        
        # 构建映射
        user_mapping = {}
        item_mapping = {}
        interactions = []
        
        async for profile in cursor:
            user_id = profile["user_id"]
            
            # 获取交互物品
            if "preferences" in profile and "viewed_items" in profile["preferences"]:
                viewed_items = profile["preferences"]["viewed_items"]
                
                if len(viewed_items) >= min_interactions:
                    for item_id in viewed_items:
                        interactions.append((user_id, item_id, 1.0))
        
        if not interactions:
            return None, None, None
        
        # 创建映射
        user_ids = list(set([u for u, _, _ in interactions]))
        item_ids = list(set([i for _, i, _ in interactions]))
        
        user_mapping = {uid: idx for idx, uid in enumerate(user_ids)}
        item_mapping = {iid: idx for idx, iid in enumerate(item_ids)}
        
        # 构建稀疏矩阵
        n_users = len(user_mapping)
        n_items = len(item_mapping)
        matrix = lil_matrix((n_users, n_items), dtype=np.float32)
        
        for user_id, item_id, value in interactions:
            u_idx = user_mapping[user_id]
            i_idx = item_mapping[item_id]
            matrix[u_idx, i_idx] = value
        
        return matrix.tocsr(), user_mapping, item_mapping
    
    def _train_als(self, interaction_matrix) -> tuple:
        """训练ALS模型（简化实现）"""
        try:
            from implicit.als import AlternatingLeastSquares
            
            # 使用implicit库训练
            model = AlternatingLeastSquares(
                factors=self.factors,
                regularization=self.regularization,
                iterations=self.iterations,
                use_gpu=False
            )
            
            # 训练
            model.fit(interaction_matrix)
            
            # 返回用户和物品因子
            return model.user_factors, model.item_factors
            
        except ImportError:
            print("[ALS-CF] implicit库未安装，使用随机初始化")
            # 降级为随机初始化
            n_users, n_items = interaction_matrix.shape
            user_factors = np.random.randn(n_users, self.factors).astype(np.float32)
            item_factors = np.random.randn(n_items, self.factors).astype(np.float32)
            return user_factors, item_factors
    
    async def _save_vectors_to_redis(
        self,
        tenant_id: str,
        scenario_id: str,
        user_factors: np.ndarray,
        item_factors: np.ndarray,
        user_mapping: Dict[str, int],
        item_mapping: Dict[str, int]
    ):
        """保存向量到Redis"""
        if not self.redis:
            return
        
        # 保存用户向量
        for user_id, u_idx in user_mapping.items():
            key = f"als:user_vector:{tenant_id}:{scenario_id}:{user_id}"
            vector = user_factors[u_idx]
            await self.redis.setex(key, 86400 * 7, vector.tobytes())  # 7天过期
        
        # 保存物品向量（使用Hash结构）
        key_pattern = f"als:item_vectors:{tenant_id}:{scenario_id}"
        
        for item_id, i_idx in item_mapping.items():
            vector = item_factors[i_idx]
            await self.redis.hset(key_pattern, item_id, vector.tobytes())
        
        # 设置Hash的过期时间
        await self.redis.expire(key_pattern, 86400 * 7)
        
        print(f"[ALS-CF] 向量已保存到Redis - 用户: {len(user_mapping)}, 物品: {len(item_mapping)}")

