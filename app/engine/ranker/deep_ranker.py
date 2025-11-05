"""
深度学习排序器

使用DeepFM等深度模型进行精排
"""
import torch
import numpy as np
from typing import List, Dict, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ml.models.deepfm import DeepFM


class DeepRanker:
    """
    深度排序器
    
    使用DeepFM模型对召回的物品进行精排
    """
    
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        model_path: str = None
    ):
        self.db = db
        self.model_path = model_path
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 特征配置
        self.sparse_features = [
            {"name": "user_id", "vocab_size": 100000},
            {"name": "item_id", "vocab_size": 100000},
            {"name": "category", "vocab_size": 1000},
            {"name": "hour", "vocab_size": 24},
            {"name": "weekday", "vocab_size": 7}
        ]
        
        self.dense_features = [
            {"name": "item_age_days", "dim": 1},
            {"name": "user_active_days", "dim": 1},
            {"name": "item_hot_score", "dim": 1}
        ]
        
        # 懒加载模型
        if model_path:
            self._load_model()
    
    def _load_model(self):
        """加载训练好的模型"""
        try:
            config = {
                "sparse_features": self.sparse_features,
                "dense_features": self.dense_features,
                "embedding_dim": 16,
                "dnn_hidden_dims": [256, 128, 64],
                "dropout": 0.3
            }
            
            self.model = DeepFM(config)
            
            if self.model_path:
                state_dict = torch.load(self.model_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
            
            self.model.to(self.device)
            self.model.eval()
            
            print(f"[DeepRanker] 模型加载成功: {self.model_path}")
        except Exception as e:
            print(f"[DeepRanker] 模型加载失败: {e}")
            self.model = None
    
    async def rank(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        item_ids: List[str]
    ) -> List[Tuple[str, float]]:
        """
        对召回的物品进行排序
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            user_id: 用户ID
            item_ids: 召回的物品ID列表
            
        Returns:
            排序后的 (item_id, score) 列表
        """
        if not item_ids:
            return []
        
        # 如果模型未加载，使用简单排序
        if not self.model:
            print("[DeepRanker] 模型未加载，使用随机排序")
            import random
            scored_items = [(item_id, random.random()) for item_id in item_ids]
            return sorted(scored_items, key=lambda x: x[1], reverse=True)
        
        try:
            # 1. 构造特征
            features = await self._build_features(
                tenant_id, scenario_id, user_id, item_ids
            )
            
            # 2. 批量预测
            scores = self._batch_predict(features)
            
            # 3. 组合结果并排序
            scored_items = list(zip(item_ids, scores))
            scored_items.sort(key=lambda x: x[1], reverse=True)
            
            return scored_items
            
        except Exception as e:
            print(f"[DeepRanker] 排序失败: {e}")
            # 降级为随机排序
            import random
            scored_items = [(item_id, random.random()) for item_id in item_ids]
            return sorted(scored_items, key=lambda x: x[1], reverse=True)
    
    async def _build_features(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        item_ids: List[str]
    ) -> Dict[str, np.ndarray]:
        """
        构造特征
        
        Returns:
            特征字典，每个key对应一个特征列，value是numpy数组
        """
        from datetime import datetime
        
        batch_size = len(item_ids)
        
        # 获取用户画像
        user_profile = await self.db.user_profiles.find_one({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "scenario_id": scenario_id
        })
        
        # 获取物品信息（批量）
        items_cursor = self.db.items.find({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "item_id": {"$in": item_ids}
        })
        items_data = {item["item_id"]: item async for item in items_cursor}
        
        # ===== 构造稀疏特征 =====
        features = {}
        
        # user_id (hash取模)
        user_id_hash = hash(user_id) % self.sparse_features[0]["vocab_size"]
        features["user_id"] = np.array([user_id_hash] * batch_size, dtype=np.int64)
        
        # item_id (hash取模)
        item_id_hashes = [
            hash(item_id) % self.sparse_features[1]["vocab_size"]
            for item_id in item_ids
        ]
        features["item_id"] = np.array(item_id_hashes, dtype=np.int64)
        
        # category (从物品元数据中提取)
        categories = []
        for item_id in item_ids:
            item = items_data.get(item_id, {})
            category = item.get("metadata", {}).get("category", "unknown")
            category_hash = hash(category) % self.sparse_features[2]["vocab_size"]
            categories.append(category_hash)
        features["category"] = np.array(categories, dtype=np.int64)
        
        # hour (当前小时)
        current_hour = datetime.utcnow().hour
        features["hour"] = np.array([current_hour] * batch_size, dtype=np.int64)
        
        # weekday (当前星期几)
        current_weekday = datetime.utcnow().weekday()
        features["weekday"] = np.array([current_weekday] * batch_size, dtype=np.int64)
        
        # ===== 构造稠密特征 =====
        
        # item_age_days (物品发布天数)
        item_ages = []
        for item_id in item_ids:
            item = items_data.get(item_id, {})
            created_at = item.get("created_at", datetime.utcnow())
            age_days = (datetime.utcnow() - created_at).days
            item_ages.append(float(age_days))
        features["item_age_days"] = np.array(item_ages, dtype=np.float32).reshape(-1, 1)
        
        # user_active_days (用户活跃天数)
        if user_profile and "created_at" in user_profile:
            active_days = (datetime.utcnow() - user_profile["created_at"]).days
        else:
            active_days = 0.0
        features["user_active_days"] = np.array([float(active_days)] * batch_size, dtype=np.float32).reshape(-1, 1)
        
        # item_hot_score (物品热度分)
        # 简化版：后续可以从Redis读取实时热度
        features["item_hot_score"] = np.random.rand(batch_size, 1).astype(np.float32)
        
        return features
    
    def _batch_predict(self, features: Dict[str, np.ndarray]) -> List[float]:
        """
        批量预测
        
        Args:
            features: 特征字典
            
        Returns:
            预测分数列表
        """
        # 转换为Tensor
        inputs = {}
        for key, value in features.items():
            inputs[key] = torch.from_numpy(value).to(self.device)
        
        # 推理
        with torch.no_grad():
            outputs = self.model(inputs)
            scores = outputs.cpu().numpy().flatten().tolist()
        
        return scores
    
    def reload_model(self, model_path: str):
        """重新加载模型（用于在线更新）"""
        self.model_path = model_path
        self._load_model()

