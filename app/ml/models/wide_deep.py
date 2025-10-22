"""
Wide & Deep模型
论文: Wide & Deep Learning for Recommender Systems (Google, 2016)

架构:
- Wide部分: 线性模型（记忆能力）
- Deep部分: DNN（泛化能力）
- 联合训练
"""
import torch
import torch.nn as nn
from typing import Dict, Any, List
from app.ml.models.base import BaseRecommenderModel, EmbeddingLayer, DNNLayer


class WideAndDeep(BaseRecommenderModel):
    """
    Wide & Deep模型
    
    适用场景: 需要同时考虑记忆和泛化的推荐场景
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: 配置字典
                - sparse_features: 稀疏特征配置 [{name, vocab_size, embed_dim}, ...]
                - dense_features: 稠密特征配置 [{name, dim}, ...]
                - dnn_hidden_dims: DNN隐层维度 [256, 128, 64]
                - dropout: Dropout比例
        """
        super().__init__(config)
        
        self.sparse_features = config.get("sparse_features", [])
        self.dense_features = config.get("dense_features", [])
        self.dnn_hidden_dims = config.get("dnn_hidden_dims", [256, 128, 64])
        self.dropout = config.get("dropout", 0.3)
        
        # Wide部分：线性层
        self.wide_dim = len(self.sparse_features) + sum(f["dim"] for f in self.dense_features)
        self.wide_layer = nn.Linear(self.wide_dim, 1)
        
        # Deep部分：Embedding + DNN
        # 1. Embedding层
        self.embeddings = nn.ModuleDict({
            f["name"]: EmbeddingLayer(f["vocab_size"], f["embed_dim"])
            for f in self.sparse_features
        })
        
        # 2. DNN输入维度
        dnn_input_dim = (
            sum(f["embed_dim"] for f in self.sparse_features) +
            sum(f["dim"] for f in self.dense_features)
        )
        
        # 3. DNN层
        self.dnn = DNNLayer(
            input_dim=dnn_input_dim,
            hidden_dims=self.dnn_hidden_dims,
            dropout=self.dropout
        )
        
        # 4. 输出层
        self.dnn_output = nn.Linear(self.dnn_hidden_dims[-1], 1)
        
        # 最终输出
        self.output_activation = nn.Sigmoid()
    
    def forward(self, inputs: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        前向传播
        
        Args:
            inputs: 输入字典
                - sparse features: {feature_name: tensor}
                - dense features: {feature_name: tensor}
                
        Returns:
            预测分数 [batch_size, 1]
        """
        batch_size = next(iter(inputs.values())).size(0)
        
        # ===== Wide部分 =====
        wide_inputs = []
        
        # 稀疏特征（One-hot）
        for f in self.sparse_features:
            feat = inputs[f["name"]]
            # One-hot编码（简化，实际可能需要更复杂处理）
            wide_inputs.append(feat.float().unsqueeze(-1))
        
        # 稠密特征
        for f in self.dense_features:
            feat = inputs[f["name"]]
            if feat.dim() == 1:
                feat = feat.unsqueeze(-1)
            wide_inputs.append(feat)
        
        wide_input = torch.cat(wide_inputs, dim=-1)
        wide_output = self.wide_layer(wide_input)
        
        # ===== Deep部分 =====
        deep_inputs = []
        
        # 稀疏特征Embedding
        for f in self.sparse_features:
            feat = inputs[f["name"]]
            embed = self.embeddings[f["name"]](feat.long())
            if embed.dim() == 3:
                # 多值特征，需要聚合
                embed = embed.mean(dim=1)
            deep_inputs.append(embed)
        
        # 稠密特征
        for f in self.dense_features:
            feat = inputs[f["name"]]
            if feat.dim() == 1:
                feat = feat.unsqueeze(-1)
            deep_inputs.append(feat)
        
        deep_input = torch.cat(deep_inputs, dim=-1)
        deep_hidden = self.dnn(deep_input)
        deep_output = self.dnn_output(deep_hidden)
        
        # ===== 融合 =====
        output = wide_output + deep_output
        output = self.output_activation(output)
        
        return output.squeeze(-1)


# 使用示例
def create_wide_deep_model() -> WideAndDeep:
    """创建Wide & Deep模型示例"""
    
    config = {
        "model_name": "wide_and_deep",
        "sparse_features": [
            {"name": "user_id", "vocab_size": 100000, "embed_dim": 32},
            {"name": "item_id", "vocab_size": 50000, "embed_dim": 32},
            {"name": "category", "vocab_size": 100, "embed_dim": 16},
            {"name": "author", "vocab_size": 10000, "embed_dim": 16}
        ],
        "dense_features": [
            {"name": "user_age", "dim": 1},
            {"name": "user_activity", "dim": 1},
            {"name": "item_duration", "dim": 1},
            {"name": "item_hot_score", "dim": 1}
        ],
        "dnn_hidden_dims": [256, 128, 64],
        "dropout": 0.3
    }
    
    model = WideAndDeep(config)
    print(f"[Wide & Deep] 模型信息: {model.get_model_info()}")
    
    return model


if __name__ == '__main__':
    # 测试
    model = create_wide_deep_model()
    
    # 模拟输入
    batch_size = 32
    inputs = {
        "user_id": torch.randint(0, 100000, (batch_size,)),
        "item_id": torch.randint(0, 50000, (batch_size,)),
        "category": torch.randint(0, 100, (batch_size,)),
        "author": torch.randint(0, 10000, (batch_size,)),
        "user_age": torch.randn(batch_size, 1),
        "user_activity": torch.randn(batch_size, 1),
        "item_duration": torch.randn(batch_size, 1),
        "item_hot_score": torch.randn(batch_size, 1)
    }
    
    # 预测
    outputs = model(inputs)
    print(f"输出形状: {outputs.shape}")
    print(f"预测分数: {outputs[:5]}")

