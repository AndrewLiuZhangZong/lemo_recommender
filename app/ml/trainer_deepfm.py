"""
DeepFM模型训练器

从ClickHouse拉取行为数据，训练DeepFM模型
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from sklearn.metrics import roc_auc_score, log_loss

from app.ml.models.deepfm import DeepFM


class CTRDataset(Dataset):
    """CTR预估数据集"""
    
    def __init__(self, features: Dict[str, np.ndarray], labels: np.ndarray):
        self.features = features
        self.labels = labels
        self.length = len(labels)
    
    def __len__(self):
        return self.length
    
    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.features.items()}
        label = torch.tensor(self.labels[idx], dtype=torch.float32)
        return item, label


class DeepFMTrainer:
    """
    DeepFM训练器
    
    功能:
    1. 从ClickHouse拉取行为数据
    2. 特征工程
    3. 模型训练
    4. 模型评估
    5. 保存模型
    """
    
    def __init__(
        self,
        tenant_id: str,
        scenario_id: str,
        db=None,
        clickhouse_client=None
    ):
        self.tenant_id = tenant_id
        self.scenario_id = scenario_id
        self.db = db
        self.clickhouse = clickhouse_client
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"[DeepFMTrainer] 初始化 - 租户: {tenant_id}, 场景: {scenario_id}")
        print(f"[DeepFMTrainer] 设备: {self.device}")
    
    async def train(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        训练模型
        
        Args:
            config: 训练配置
                - days: 数据天数（默认7天）
                - batch_size: 批大小（默认256）
                - epochs: 训练轮数（默认10）
                - learning_rate: 学习率（默认0.001）
                - negative_ratio: 负样本比例（默认4）
                
        Returns:
            训练结果
        """
        config = config or {}
        
        days = config.get("days", 7)
        batch_size = config.get("batch_size", 256)
        epochs = config.get("epochs", 10)
        learning_rate = config.get("learning_rate", 0.001)
        
        print(f"\n[DeepFMTrainer] 训练配置:")
        print(f"  - 数据天数: {days}")
        print(f"  - Batch Size: {batch_size}")
        print(f"  - Epochs: {epochs}")
        print(f"  - Learning Rate: {learning_rate}")
        
        # 1. 准备数据
        print(f"\n[Step 1/5] 准备训练数据...")
        train_features, train_labels, test_features, test_labels = await self._prepare_data(days, config)
        
        if len(train_labels) == 0:
            return {
                "success": False,
                "error": "训练数据为空"
            }
        
        print(f"  - 训练样本: {len(train_labels)}")
        print(f"  - 测试样本: {len(test_labels)}")
        print(f"  - 正样本比例: {train_labels.mean():.4f}")
        
        # 2. 创建数据集
        train_dataset = CTRDataset(train_features, train_labels)
        test_dataset = CTRDataset(test_features, test_labels)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
        
        # 3. 构建模型
        print(f"\n[Step 2/5] 构建模型...")
        model_config = {
            "sparse_features": [
                {"name": "user_id", "vocab_size": 100000},
                {"name": "item_id", "vocab_size": 100000},
                {"name": "category", "vocab_size": 1000},
                {"name": "hour", "vocab_size": 24},
                {"name": "weekday", "vocab_size": 7}
            ],
            "dense_features": [
                {"name": "item_age_days", "dim": 1},
                {"name": "user_active_days", "dim": 1},
                {"name": "item_hot_score", "dim": 1}
            ],
            "embedding_dim": 16,
            "dnn_hidden_dims": [256, 128, 64],
            "dropout": 0.3
        }
        
        model = DeepFM(model_config).to(self.device)
        criterion = nn.BCELoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        
        # 4. 训练模型
        print(f"\n[Step 3/5] 开始训练...")
        best_auc = 0.0
        best_model_state = None
        
        for epoch in range(epochs):
            # 训练
            model.train()
            train_loss = 0.0
            for batch_features, batch_labels in train_loader:
                # 转移到设备
                batch_features = {k: v.to(self.device) for k, v in batch_features.items()}
                batch_labels = batch_labels.to(self.device)
                
                # 前向传播
                predictions = model(batch_features).squeeze()
                loss = criterion(predictions, batch_labels)
                
                # 反向传播
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            avg_train_loss = train_loss / len(train_loader)
            
            # 评估
            model.eval()
            test_preds = []
            test_trues = []
            
            with torch.no_grad():
                for batch_features, batch_labels in test_loader:
                    batch_features = {k: v.to(self.device) for k, v in batch_features.items()}
                    predictions = model(batch_features).squeeze()
                    test_preds.extend(predictions.cpu().numpy())
                    test_trues.extend(batch_labels.numpy())
            
            # 计算指标
            test_auc = roc_auc_score(test_trues, test_preds)
            test_loss = log_loss(test_trues, test_preds)
            
            print(f"  Epoch {epoch+1}/{epochs}: "
                  f"Train Loss={avg_train_loss:.4f}, "
                  f"Test AUC={test_auc:.4f}, "
                  f"Test Loss={test_loss:.4f}")
            
            # 保存最优模型
            if test_auc > best_auc:
                best_auc = test_auc
                best_model_state = model.state_dict().copy()
        
        # 5. 保存模型
        print(f"\n[Step 4/5] 保存模型...")
        model_path = f"models/deepfm_{self.tenant_id}_{self.scenario_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pt"
        
        if best_model_state:
            torch.save(best_model_state, model_path)
            print(f"  - 模型已保存: {model_path}")
            print(f"  - 最佳AUC: {best_auc:.4f}")
        
        # 6. 返回结果
        result = {
            "success": True,
            "tenant_id": self.tenant_id,
            "scenario_id": self.scenario_id,
            "model_path": model_path,
            "metrics": {
                "best_auc": float(best_auc),
                "train_samples": len(train_labels),
                "test_samples": len(test_labels)
            },
            "trained_at": datetime.utcnow().isoformat()
        }
        
        print(f"\n[Step 5/5] 训练完成!")
        return result
    
    async def _prepare_data(
        self,
        days: int,
        config: Dict[str, Any]
    ) -> Tuple[Dict[str, np.ndarray], np.ndarray, Dict[str, np.ndarray], np.ndarray]:
        """
        准备训练数据
        
        Returns:
            (train_features, train_labels, test_features, test_labels)
        """
        # 这里是简化版，实际应该从ClickHouse拉取
        # 现在生成模拟数据
        print(f"  [Warning] 使用模拟数据，生产环境请从ClickHouse获取真实数据")
        
        # 模拟10000条训练数据
        num_samples = 10000
        
        features = {
            "user_id": np.random.randint(0, 10000, size=num_samples),
            "item_id": np.random.randint(0, 5000, size=num_samples),
            "category": np.random.randint(0, 100, size=num_samples),
            "hour": np.random.randint(0, 24, size=num_samples),
            "weekday": np.random.randint(0, 7, size=num_samples),
            "item_age_days": np.random.rand(num_samples, 1).astype(np.float32) * 30,
            "user_active_days": np.random.rand(num_samples, 1).astype(np.float32) * 100,
            "item_hot_score": np.random.rand(num_samples, 1).astype(np.float32)
        }
        
        # 模拟标签（CTR=10%）
        labels = (np.random.rand(num_samples) < 0.1).astype(np.float32)
        
        # 切分训练/测试集（8:2）
        split_idx = int(num_samples * 0.8)
        
        train_features = {k: v[:split_idx] for k, v in features.items()}
        train_labels = labels[:split_idx]
        
        test_features = {k: v[split_idx:] for k, v in features.items()}
        test_labels = labels[split_idx:]
        
        return train_features, train_labels, test_features, test_labels
    
    async def _fetch_from_clickhouse(self, days: int) -> List[Dict[str, Any]]:
        """从ClickHouse拉取行为数据（实际实现）"""
        # TODO: 实现从ClickHouse拉取数据
        # SELECT user_id, item_id, behavior_type, created_at
        # FROM user_behaviors
        # WHERE tenant_id = ? AND scenario_id = ?
        #   AND created_at >= now() - INTERVAL ? DAY
        pass

