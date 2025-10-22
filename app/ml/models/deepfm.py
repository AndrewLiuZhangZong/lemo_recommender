"""
DeepFM模型
论文: DeepFM: A Factorization-Machine based Neural Network for CTR Prediction (2017)

架构:
- FM部分: 一阶特征 + 二阶交叉特征（特征交互）
- Deep部分: DNN（高阶特征组合）
- 共享Embedding层
"""
import torch
import torch.nn as nn
from typing import Dict, Any, List
from app.ml.models.base import BaseRecommenderModel, EmbeddingLayer, DNNLayer


class FM(nn.Module):
    """
    Factorization Machine层
    计算一阶特征和二阶交叉特征
    """
    
    def __init__(self):
        super().__init__()
    
    def forward(self, embeddings: torch.Tensor) -> torch.Tensor:
        """
        Args:
            embeddings: [batch_size, num_fields, embed_dim]
            
        Returns:
            二阶交叉特征 [batch_size, 1]
        """
        # sum(x_i * x_j) = 0.5 * [sum(x)^2 - sum(x^2)]
        square_of_sum = torch.sum(embeddings, dim=1) ** 2  # [batch, embed_dim]
        sum_of_square = torch.sum(embeddings ** 2, dim=1)  # [batch, embed_dim]
        
        fm_output = 0.5 * torch.sum(square_of_sum - sum_of_square, dim=1, keepdim=True)
        
        return fm_output


class DeepFM(BaseRecommenderModel):
    """
    DeepFM模型
    
    适用场景: 点击率预估、转化率预估
    特点: 自动学习特征交互，无需手工特征工程
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: 配置字典
                - sparse_features: 稀疏特征配置
                - dense_features: 稠密特征配置
                - embedding_dim: 统一的Embedding维度
                - dnn_hidden_dims: DNN隐层维度
                - dropout: Dropout比例
        """
        super().__init__(config)
        
        self.sparse_features = config.get("sparse_features", [])
        self.dense_features = config.get("dense_features", [])
        self.embedding_dim = config.get("embedding_dim", 16)
        self.dnn_hidden_dims = config.get("dnn_hidden_dims", [256, 128, 64])
        self.dropout = config.get("dropout", 0.3)
        
        # ===== Embedding层（FM和Deep共享） =====
        self.embeddings = nn.ModuleDict({
            f["name"]: EmbeddingLayer(f["vocab_size"], self.embedding_dim)
            for f in self.sparse_features
        })
        
        # 稠密特征的线性变换（转为embedding维度）
        self.dense_embeddings = nn.ModuleDict({
            f["name"]: nn.Linear(f["dim"], self.embedding_dim)
            for f in self.dense_features
        })
        
        # ===== FM部分 =====
        # 一阶特征
        num_features = len(self.sparse_features) + len(self.dense_features)
        self.fm_first_order = nn.Linear(num_features, 1)
        
        # 二阶交叉特征
        self.fm = FM()
        
        # ===== Deep部分 =====
        dnn_input_dim = num_features * self.embedding_dim
        self.dnn = DNNLayer(
            input_dim=dnn_input_dim,
            hidden_dims=self.dnn_hidden_dims,
            dropout=self.dropout
        )
        self.dnn_output = nn.Linear(self.dnn_hidden_dims[-1], 1)
        
        # 输出激活
        self.output_activation = nn.Sigmoid()
    
    def forward(self, inputs: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        前向传播
        
        Args:
            inputs: 输入字典
            
        Returns:
            预测分数 [batch_size]
        """
        batch_size = next(iter(inputs.values())).size(0)
        
        # ===== 特征处理 =====
        embeddings = []  # 用于FM和Deep
        first_order_inputs = []  # 用于FM一阶
        
        # 稀疏特征
        for f in self.sparse_features:
            feat = inputs[f["name"]].long()
            embed = self.embeddings[f["name"]](feat)
            if embed.dim() == 3:
                embed = embed.mean(dim=1)
            embeddings.append(embed)
            first_order_inputs.append(feat.float().unsqueeze(-1))
        
        # 稠密特征
        for f in self.dense_features:
            feat = inputs[f["name"]]
            if feat.dim() == 1:
                feat = feat.unsqueeze(-1)
            embed = self.dense_embeddings[f["name"]](feat)
            embeddings.append(embed)
            first_order_inputs.append(feat.mean(dim=-1, keepdim=True))
        
        # [batch_size, num_fields, embed_dim]
        embeddings_tensor = torch.stack(embeddings, dim=1)
        
        # ===== FM部分 =====
        # 一阶特征
        first_order_tensor = torch.cat(first_order_inputs, dim=-1)
        fm_first_order_output = self.fm_first_order(first_order_tensor)
        
        # 二阶交叉特征
        fm_second_order_output = self.fm(embeddings_tensor)
        
        fm_output = fm_first_order_output + fm_second_order_output
        
        # ===== Deep部分 =====
        # 展平embeddings
        deep_input = embeddings_tensor.view(batch_size, -1)
        deep_hidden = self.dnn(deep_input)
        deep_output = self.dnn_output(deep_hidden)
        
        # ===== 融合输出 =====
        output = fm_output + deep_output
        output = self.output_activation(output)
        
        return output.squeeze(-1)


# 使用示例
def create_deepfm_model() -> DeepFM:
    """创建DeepFM模型示例"""
    
    config = {
        "model_name": "deepfm",
        "sparse_features": [
            {"name": "user_id", "vocab_size": 100000},
            {"name": "item_id", "vocab_size": 50000},
            {"name": "category", "vocab_size": 100},
            {"name": "author", "vocab_size": 10000},
            {"name": "device", "vocab_size": 10},
            {"name": "city", "vocab_size": 500}
        ],
        "dense_features": [
            {"name": "user_age", "dim": 1},
            {"name": "item_duration", "dim": 1},
            {"name": "item_hot_score", "dim": 1},
            {"name": "hour_of_day", "dim": 1}
        ],
        "embedding_dim": 16,
        "dnn_hidden_dims": [256, 128, 64],
        "dropout": 0.3
    }
    
    model = DeepFM(config)
    print(f"[DeepFM] 模型信息: {model.get_model_info()}")
    
    return model


if __name__ == '__main__':
    # 测试
    model = create_deepfm_model()
    
    # 模拟输入
    batch_size = 32
    inputs = {
        "user_id": torch.randint(0, 100000, (batch_size,)),
        "item_id": torch.randint(0, 50000, (batch_size,)),
        "category": torch.randint(0, 100, (batch_size,)),
        "author": torch.randint(0, 10000, (batch_size,)),
        "device": torch.randint(0, 10, (batch_size,)),
        "city": torch.randint(0, 500, (batch_size,)),
        "user_age": torch.randn(batch_size, 1),
        "item_duration": torch.randn(batch_size, 1),
        "item_hot_score": torch.randn(batch_size, 1),
        "hour_of_day": torch.randn(batch_size, 1)
    }
    
    # 预测
    outputs = model(inputs)
    print(f"输出形状: {outputs.shape}")
    print(f"预测分数: {outputs[:5]}")

