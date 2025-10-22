"""
双塔召回模型 (Two-Tower Model / DSSM)
论文: Learning Deep Structured Semantic Models for Web Search (Microsoft, 2013)

架构:
- User Tower: 用户特征 → DNN → 用户向量
- Item Tower: 物品特征 → DNN → 物品向量
- 相似度: cosine(user_vector, item_vector)

优势:
- 用户和物品向量可离线预计算
- 线上只需向量检索，性能极高
- 适合大规模召回场景
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, List, Tuple
from app.ml.models.base import BaseRecommenderModel, EmbeddingLayer, DNNLayer


class TowerModel(nn.Module):
    """
    单塔模型（User塔或Item塔）
    """
    
    def __init__(
        self,
        sparse_features: List[Dict[str, Any]],
        dense_features: List[Dict[str, Any]],
        embedding_dim: int,
        dnn_hidden_dims: List[int],
        output_dim: int,
        dropout: float = 0.3
    ):
        super().__init__()
        
        self.sparse_features = sparse_features
        self.dense_features = dense_features
        self.embedding_dim = embedding_dim
        self.output_dim = output_dim
        
        # Embedding层
        self.embeddings = nn.ModuleDict({
            f["name"]: EmbeddingLayer(f["vocab_size"], embedding_dim)
            for f in sparse_features
        })
        
        # DNN输入维度
        dnn_input_dim = (
            len(sparse_features) * embedding_dim +
            sum(f["dim"] for f in dense_features)
        )
        
        # DNN层
        self.dnn = DNNLayer(
            input_dim=dnn_input_dim,
            hidden_dims=dnn_hidden_dims,
            dropout=dropout
        )
        
        # 输出层（向量）
        self.output_layer = nn.Linear(dnn_hidden_dims[-1], output_dim)
    
    def forward(self, inputs: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Args:
            inputs: 特征字典
            
        Returns:
            输出向量 [batch_size, output_dim]
        """
        embeddings = []
        
        # 稀疏特征
        for f in self.sparse_features:
            if f["name"] in inputs:
                feat = inputs[f["name"]].long()
                embed = self.embeddings[f["name"]](feat)
                if embed.dim() == 3:
                    embed = embed.mean(dim=1)
                embeddings.append(embed)
        
        # 稠密特征
        for f in self.dense_features:
            if f["name"] in inputs:
                feat = inputs[f["name"]]
                if feat.dim() == 1:
                    feat = feat.unsqueeze(-1)
                embeddings.append(feat)
        
        # 拼接
        tower_input = torch.cat(embeddings, dim=-1)
        
        # DNN
        hidden = self.dnn(tower_input)
        output = self.output_layer(hidden)
        
        # L2归一化（用于余弦相似度）
        output = F.normalize(output, p=2, dim=1)
        
        return output


class TwoTowerModel(BaseRecommenderModel):
    """
    双塔召回模型
    
    适用场景: 大规模候选集召回
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: 配置字典
                - user_sparse_features: 用户稀疏特征
                - user_dense_features: 用户稠密特征
                - item_sparse_features: 物品稀疏特征
                - item_dense_features: 物品稠密特征
                - embedding_dim: Embedding维度
                - user_dnn_hidden_dims: User塔DNN维度
                - item_dnn_hidden_dims: Item塔DNN维度
                - output_dim: 输出向量维度
                - temperature: 温度参数
        """
        super().__init__(config)
        
        self.embedding_dim = config.get("embedding_dim", 16)
        self.output_dim = config.get("output_dim", 128)
        self.temperature = config.get("temperature", 0.1)
        
        # User塔
        self.user_tower = TowerModel(
            sparse_features=config.get("user_sparse_features", []),
            dense_features=config.get("user_dense_features", []),
            embedding_dim=self.embedding_dim,
            dnn_hidden_dims=config.get("user_dnn_hidden_dims", [256, 128]),
            output_dim=self.output_dim,
            dropout=config.get("dropout", 0.3)
        )
        
        # Item塔
        self.item_tower = TowerModel(
            sparse_features=config.get("item_sparse_features", []),
            dense_features=config.get("item_dense_features", []),
            embedding_dim=self.embedding_dim,
            dnn_hidden_dims=config.get("item_dnn_hidden_dims", [256, 128]),
            output_dim=self.output_dim,
            dropout=config.get("dropout", 0.3)
        )
    
    def forward(
        self,
        inputs: Dict[str, torch.Tensor]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播
        
        Args:
            inputs: 输入字典，包含user和item特征
            
        Returns:
            (user_vectors, item_vectors)
        """
        # 分离user和item输入
        user_inputs = {k: v for k, v in inputs.items() if k.startswith("user_")}
        item_inputs = {k: v for k, v in inputs.items() if k.startswith("item_")}
        
        # 计算向量
        user_vectors = self.user_tower(user_inputs)
        item_vectors = self.item_tower(item_inputs)
        
        return user_vectors, item_vectors
    
    def compute_similarity(
        self,
        user_vectors: torch.Tensor,
        item_vectors: torch.Tensor
    ) -> torch.Tensor:
        """
        计算相似度分数
        
        Args:
            user_vectors: [batch_size, output_dim]
            item_vectors: [batch_size, output_dim] or [num_items, output_dim]
            
        Returns:
            相似度分数
        """
        # 余弦相似度
        if user_vectors.dim() == 2 and item_vectors.dim() == 2:
            if user_vectors.size(0) == item_vectors.size(0):
                # 点对点
                similarity = torch.sum(user_vectors * item_vectors, dim=1)
            else:
                # 矩阵乘法 [batch, output_dim] x [output_dim, num_items]
                similarity = torch.matmul(user_vectors, item_vectors.t())
        else:
            raise ValueError("Unsupported vector dimensions")
        
        # 温度缩放
        similarity = similarity / self.temperature
        
        return similarity
    
    def encode_user(self, user_inputs: Dict[str, torch.Tensor]) -> torch.Tensor:
        """编码用户（用于离线预计算）"""
        return self.user_tower(user_inputs)
    
    def encode_item(self, item_inputs: Dict[str, torch.Tensor]) -> torch.Tensor:
        """编码物品（用于离线预计算）"""
        return self.item_tower(item_inputs)


# 使用示例
def create_two_tower_model() -> TwoTowerModel:
    """创建双塔模型示例"""
    
    config = {
        "model_name": "two_tower",
        # User特征
        "user_sparse_features": [
            {"name": "user_id", "vocab_size": 100000},
            {"name": "user_gender", "vocab_size": 3},
            {"name": "user_city", "vocab_size": 500}
        ],
        "user_dense_features": [
            {"name": "user_age", "dim": 1},
            {"name": "user_activity_score", "dim": 1}
        ],
        # Item特征
        "item_sparse_features": [
            {"name": "item_id", "vocab_size": 50000},
            {"name": "item_category", "vocab_size": 100},
            {"name": "item_author", "vocab_size": 10000}
        ],
        "item_dense_features": [
            {"name": "item_duration", "dim": 1},
            {"name": "item_hot_score", "dim": 1}
        ],
        # 模型参数
        "embedding_dim": 16,
        "user_dnn_hidden_dims": [256, 128],
        "item_dnn_hidden_dims": [256, 128],
        "output_dim": 128,
        "temperature": 0.1,
        "dropout": 0.3
    }
    
    model = TwoTowerModel(config)
    print(f"[Two-Tower] 模型信息: {model.get_model_info()}")
    
    return model


if __name__ == '__main__':
    # 测试
    model = create_two_tower_model()
    
    # 模拟输入
    batch_size = 32
    inputs = {
        # User特征
        "user_id": torch.randint(0, 100000, (batch_size,)),
        "user_gender": torch.randint(0, 3, (batch_size,)),
        "user_city": torch.randint(0, 500, (batch_size,)),
        "user_age": torch.randn(batch_size, 1),
        "user_activity_score": torch.randn(batch_size, 1),
        # Item特征
        "item_id": torch.randint(0, 50000, (batch_size,)),
        "item_category": torch.randint(0, 100, (batch_size,)),
        "item_author": torch.randint(0, 10000, (batch_size,)),
        "item_duration": torch.randn(batch_size, 1),
        "item_hot_score": torch.randn(batch_size, 1)
    }
    
    # 前向传播
    user_vectors, item_vectors = model(inputs)
    print(f"User向量: {user_vectors.shape}")
    print(f"Item向量: {item_vectors.shape}")
    
    # 计算相似度
    similarity = model.compute_similarity(user_vectors, item_vectors)
    print(f"相似度分数: {similarity.shape}")
    print(f"相似度值: {similarity[:5]}")

