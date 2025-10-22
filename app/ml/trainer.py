"""
模型训练器
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import json
from pathlib import Path


class RecommenderDataset(Dataset):
    """推荐系统数据集"""
    
    def __init__(self, data: list[Dict[str, Any]]):
        self.data = data
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        return self.data[idx]


class ModelTrainer:
    """
    模型训练器
    
    功能:
    - 训练循环
    - 验证评估
    - 模型保存/加载
    - 训练日志
    """
    
    def __init__(
        self,
        model: nn.Module,
        loss_fn: nn.Module,
        optimizer: optim.Optimizer,
        device: torch.device = None,
        model_dir: str = "models"
    ):
        self.model = model
        self.loss_fn = loss_fn
        self.optimizer = optimizer
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # 移动模型到设备
        self.model.to(self.device)
        
        # 训练历史
        self.history = {
            "train_loss": [],
            "val_loss": [],
            "metrics": []
        }
    
    def train_epoch(
        self,
        train_loader: DataLoader,
        epoch: int
    ) -> float:
        """
        训练一个epoch
        
        Args:
            train_loader: 训练数据加载器
            epoch: 当前epoch数
            
        Returns:
            平均损失
        """
        self.model.train()
        total_loss = 0
        num_batches = 0
        
        for batch_idx, batch in enumerate(train_loader):
            # 数据移到设备
            inputs = {k: v.to(self.device) for k, v in batch.items() if k != "label"}
            labels = batch["label"].to(self.device)
            
            # 前向传播
            self.optimizer.zero_grad()
            outputs = self.model(inputs)
            
            # 计算损失
            loss = self.loss_fn(outputs, labels)
            
            # 反向传播
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
            
            # 打印进度
            if batch_idx % 100 == 0:
                print(f"Epoch {epoch}, Batch {batch_idx}/{len(train_loader)}, "
                      f"Loss: {loss.item():.4f}")
        
        avg_loss = total_loss / num_batches
        return avg_loss
    
    def evaluate(
        self,
        val_loader: DataLoader,
        metrics: Optional[Dict[str, Callable]] = None
    ) -> Dict[str, float]:
        """
        评估模型
        
        Args:
            val_loader: 验证数据加载器
            metrics: 评估指标函数字典
            
        Returns:
            评估结果
        """
        self.model.eval()
        total_loss = 0
        num_batches = 0
        
        all_predictions = []
        all_labels = []
        
        with torch.no_grad():
            for batch in val_loader:
                # 数据移到设备
                inputs = {k: v.to(self.device) for k, v in batch.items() if k != "label"}
                labels = batch["label"].to(self.device)
                
                # 前向传播
                outputs = self.model(inputs)
                
                # 计算损失
                loss = self.loss_fn(outputs, labels)
                total_loss += loss.item()
                num_batches += 1
                
                # 收集预测和标签
                all_predictions.extend(outputs.cpu().numpy().tolist())
                all_labels.extend(labels.cpu().numpy().tolist())
        
        # 平均损失
        avg_loss = total_loss / num_batches
        results = {"loss": avg_loss}
        
        # 计算额外指标
        if metrics:
            for metric_name, metric_fn in metrics.items():
                results[metric_name] = metric_fn(all_labels, all_predictions)
        
        return results
    
    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: int,
        metrics: Optional[Dict[str, Callable]] = None,
        early_stopping_patience: int = 5
    ):
        """
        训练模型
        
        Args:
            train_loader: 训练数据
            val_loader: 验证数据
            num_epochs: 训练轮数
            metrics: 评估指标
            early_stopping_patience: 早停patience
        """
        print("=" * 60)
        print("  开始训练")
        print("=" * 60)
        print(f"设备: {self.device}")
        print(f"模型参数: {sum(p.numel() for p in self.model.parameters()):,}")
        print(f"训练集大小: {len(train_loader.dataset)}")
        print(f"验证集大小: {len(val_loader.dataset)}")
        print()
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(1, num_epochs + 1):
            print(f"Epoch {epoch}/{num_epochs}")
            print("-" * 60)
            
            # 训练
            train_loss = self.train_epoch(train_loader, epoch)
            self.history["train_loss"].append(train_loss)
            print(f"训练损失: {train_loss:.4f}")
            
            # 验证
            val_results = self.evaluate(val_loader, metrics)
            val_loss = val_results["loss"]
            self.history["val_loss"].append(val_loss)
            self.history["metrics"].append(val_results)
            
            print(f"验证损失: {val_loss:.4f}")
            for metric_name, metric_value in val_results.items():
                if metric_name != "loss":
                    print(f"{metric_name}: {metric_value:.4f}")
            
            # 保存最佳模型
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self.save_checkpoint(epoch, is_best=True)
                patience_counter = 0
                print("✅ 保存最佳模型")
            else:
                patience_counter += 1
            
            # Early stopping
            if patience_counter >= early_stopping_patience:
                print(f"\n早停触发（patience={early_stopping_patience}）")
                break
            
            print()
        
        print("=" * 60)
        print("  训练完成")
        print("=" * 60)
        print(f"最佳验证损失: {best_val_loss:.4f}")
    
    def save_checkpoint(self, epoch: int, is_best: bool = False):
        """保存检查点"""
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "history": self.history,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 保存最新检查点
        checkpoint_path = self.model_dir / "checkpoint_latest.pt"
        torch.save(checkpoint, checkpoint_path)
        
        # 保存最佳模型
        if is_best:
            best_path = self.model_dir / "model_best.pt"
            torch.save(checkpoint, best_path)
            
            # 保存模型配置
            if hasattr(self.model, 'config'):
                config_path = self.model_dir / "model_config.json"
                with open(config_path, 'w') as f:
                    json.dump(self.model.config, f, indent=2, ensure_ascii=False)
    
    def load_checkpoint(self, checkpoint_path: str):
        """加载检查点"""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.history = checkpoint["history"]
        
        print(f"[Trainer] 已加载检查点: {checkpoint_path}")
        print(f"  - Epoch: {checkpoint['epoch']}")
        print(f"  - Timestamp: {checkpoint['timestamp']}")


# 损失函数
class BCELossForRecommender(nn.Module):
    """二分类交叉熵损失（用于CTR预估）"""
    
    def __init__(self):
        super().__init__()
        self.bce = nn.BCELoss()
    
    def forward(self, predictions: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        return self.bce(predictions, labels.float())


class BPRLoss(nn.Module):
    """
    BPR损失（Bayesian Personalized Ranking）
    用于隐式反馈的排序学习
    """
    
    def __init__(self):
        super().__init__()
    
    def forward(
        self,
        positive_scores: torch.Tensor,
        negative_scores: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            positive_scores: 正样本分数
            negative_scores: 负样本分数
        """
        return -torch.mean(torch.log(torch.sigmoid(positive_scores - negative_scores)))

