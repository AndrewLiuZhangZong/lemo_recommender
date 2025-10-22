"""
推荐模型基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import torch
import torch.nn as nn


class BaseRecommenderModel(ABC, nn.Module):
    """推荐模型基类"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.model_name = config.get("model_name", "base_model")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    @abstractmethod
    def forward(self, inputs: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        前向传播
        
        Args:
            inputs: 输入字典，包含特征张量
            
        Returns:
            预测结果张量
        """
        pass
    
    def predict(self, inputs: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        预测
        
        Args:
            inputs: 输入字典
            
        Returns:
            预测分数
        """
        self.eval()
        with torch.no_grad():
            outputs = self.forward(inputs)
        return outputs
    
    def save_model(self, path: str):
        """保存模型"""
        torch.save({
            'model_state_dict': self.state_dict(),
            'config': self.config
        }, path)
        print(f"[Model] 已保存模型到: {path}")
    
    def load_model(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        self.load_state_dict(checkpoint['model_state_dict'])
        self.config = checkpoint['config']
        print(f"[Model] 已加载模型从: {path}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        return {
            "model_name": self.model_name,
            "total_params": total_params,
            "trainable_params": trainable_params,
            "device": str(self.device),
            "config": self.config
        }


class EmbeddingLayer(nn.Module):
    """Embedding层（通用）"""
    
    def __init__(
        self,
        num_embeddings: int,
        embedding_dim: int,
        padding_idx: int = None
    ):
        super().__init__()
        self.embedding = nn.Embedding(
            num_embeddings,
            embedding_dim,
            padding_idx=padding_idx
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.embedding(x)


class DNNLayer(nn.Module):
    """DNN层（全连接网络）"""
    
    def __init__(
        self,
        input_dim: int,
        hidden_dims: List[int],
        dropout: float = 0.3,
        activation: str = "relu"
    ):
        super().__init__()
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim))
            
            if activation == "relu":
                layers.append(nn.ReLU())
            elif activation == "leaky_relu":
                layers.append(nn.LeakyReLU())
            elif activation == "prelu":
                layers.append(nn.PReLU())
            
            layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim
        
        self.dnn = nn.Sequential(*layers)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dnn(x)

