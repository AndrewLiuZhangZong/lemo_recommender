"""
Milvus向量数据库客户端
"""
from typing import List, Dict, Optional, Any
import numpy as np


class MilvusClient:
    """
    Milvus向量数据库客户端封装
    
    功能:
    1. 物品向量存储与检索
    2. 用户向量存储与检索
    3. ANN相似度搜索
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 19530,
        enabled: bool = False
    ):
        self.host = host
        self.port = port
        self.enabled = enabled
        self.connection = None
        
        if enabled:
            self._connect()
    
    def _connect(self):
        """连接Milvus"""
        # TODO: 实际Milvus集成
        # from pymilvus import connections
        # connections.connect(
        #     alias="default",
        #     host=self.host,
        #     port=self.port
        # )
        # self.connection = connections
        print(f"[Milvus] 已连接到 {self.host}:{self.port}")
    
    async def create_collection(
        self,
        collection_name: str,
        dimension: int = 768,
        description: str = ""
    ) -> bool:
        """
        创建向量集合
        
        Args:
            collection_name: 集合名称 (如 "items_embeddings", "user_embeddings")
            dimension: 向量维度
            description: 描述
            
        Returns:
            是否成功
        """
        if not self.enabled:
            return False
        
        # TODO: 实际实现
        # from pymilvus import Collection, CollectionSchema, FieldSchema, DataType
        #
        # fields = [
        #     FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        #     FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=100),
        #     FieldSchema(name="scenario_id", dtype=DataType.VARCHAR, max_length=100),
        #     FieldSchema(name="item_id", dtype=DataType.VARCHAR, max_length=100),
        #     FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension)
        # ]
        #
        # schema = CollectionSchema(fields=fields, description=description)
        # collection = Collection(name=collection_name, schema=schema)
        #
        # # 创建索引
        # index_params = {
        #     "metric_type": "IP",  # Inner Product (余弦相似度)
        #     "index_type": "IVF_FLAT",
        #     "params": {"nlist": 1024}
        # }
        # collection.create_index(field_name="embedding", index_params=index_params)
        #
        # collection.load()
        
        print(f"[Milvus] 创建集合: {collection_name}, 维度: {dimension}")
        return True
    
    async def insert_vectors(
        self,
        collection_name: str,
        tenant_id: str,
        scenario_id: str,
        item_ids: List[str],
        embeddings: List[List[float]]
    ) -> int:
        """
        插入向量
        
        Args:
            collection_name: 集合名称
            tenant_id: 租户ID
            scenario_id: 场景ID
            item_ids: 物品ID列表
            embeddings: 向量列表
            
        Returns:
            插入数量
        """
        if not self.enabled or not item_ids:
            return 0
        
        # TODO: 实际实现
        # from pymilvus import Collection
        #
        # collection = Collection(collection_name)
        # entities = [
        #     [tenant_id] * len(item_ids),    # tenant_id
        #     [scenario_id] * len(item_ids),  # scenario_id
        #     item_ids,                       # item_id
        #     embeddings                      # embedding
        # ]
        #
        # result = collection.insert(entities)
        # collection.flush()
        
        print(f"[Milvus] 插入 {len(item_ids)} 个向量到 {collection_name}")
        return len(item_ids)
    
    async def search_similar(
        self,
        collection_name: str,
        tenant_id: str,
        scenario_id: str,
        query_embedding: List[float],
        top_k: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        相似度搜索
        
        Args:
            collection_name: 集合名称
            tenant_id: 租户ID
            scenario_id: 场景ID
            query_embedding: 查询向量
            top_k: 返回Top K个结果
            filters: 额外过滤条件
            
        Returns:
            相似物品列表 [{"item_id": "xxx", "score": 0.95}, ...]
        """
        if not self.enabled:
            return []
        
        # TODO: 实际实现
        # from pymilvus import Collection
        #
        # collection = Collection(collection_name)
        #
        # # 构建搜索表达式
        # expr = f'tenant_id == "{tenant_id}" && scenario_id == "{scenario_id}"'
        # if filters:
        #     for key, value in filters.items():
        #         expr += f' && {key} == "{value}"'
        #
        # # 搜索参数
        # search_params = {
        #     "metric_type": "IP",
        #     "params": {"nprobe": 10}
        # }
        #
        # # 执行搜索
        # results = collection.search(
        #     data=[query_embedding],
        #     anns_field="embedding",
        #     param=search_params,
        #     limit=top_k,
        #     expr=expr,
        #     output_fields=["item_id"]
        # )
        #
        # # 格式化结果
        # similar_items = []
        # for hits in results:
        #     for hit in hits:
        #         similar_items.append({
        #             "item_id": hit.entity.get("item_id"),
        #             "score": float(hit.score)
        #         })
        #
        # return similar_items
        
        print(f"[Milvus] 搜索相似向量: {collection_name}, Top {top_k}")
        # 返回模拟数据
        return [
            {"item_id": f"item_{i}", "score": 0.9 - i * 0.01}
            for i in range(min(top_k, 10))
        ]
    
    async def delete_vectors(
        self,
        collection_name: str,
        item_ids: List[str]
    ) -> int:
        """
        删除向量
        
        Args:
            collection_name: 集合名称
            item_ids: 物品ID列表
            
        Returns:
            删除数量
        """
        if not self.enabled or not item_ids:
            return 0
        
        # TODO: 实际实现
        # from pymilvus import Collection
        #
        # collection = Collection(collection_name)
        # expr = f'item_id in {item_ids}'
        # collection.delete(expr)
        
        print(f"[Milvus] 删除 {len(item_ids)} 个向量从 {collection_name}")
        return len(item_ids)
    
    def close(self):
        """关闭连接"""
        if self.enabled and self.connection:
            # TODO: 实际关闭
            # self.connection.disconnect("default")
            print("[Milvus] 已断开连接")


# Collection名称定义
class MilvusCollections:
    """Milvus集合名称定义"""
    
    @staticmethod
    def items_embeddings(scenario_type: str) -> str:
        """物品向量集合（按场景类型分）"""
        return f"items_embeddings_{scenario_type}"
    
    @staticmethod
    def user_embeddings(scenario_type: str) -> str:
        """用户向量集合（按场景类型分）"""
        return f"user_embeddings_{scenario_type}"


# 向量生成工具
class EmbeddingGenerator:
    """向量生成器（示例）"""
    
    @staticmethod
    def generate_item_embedding(item_metadata: Dict[str, Any]) -> List[float]:
        """
        生成物品向量
        
        实际生产中应使用:
        - 预训练模型 (BERT, Sentence-BERT)
        - 多模态模型 (CLIP for 图像+文本)
        - 场景特定模型
        
        Args:
            item_metadata: 物品元数据
            
        Returns:
            768维向量
        """
        # TODO: 实际向量生成
        # 使用预训练模型或训练好的embedding模型
        
        # 示例：随机向量（仅用于演示）
        np.random.seed(hash(str(item_metadata)) % 2**32)
        embedding = np.random.randn(768).tolist()
        
        # 归一化
        norm = np.linalg.norm(embedding)
        embedding = [x / norm for x in embedding]
        
        return embedding
    
    @staticmethod
    def generate_user_embedding(user_interactions: List[Dict[str, Any]]) -> List[float]:
        """
        生成用户向量（基于历史交互）
        
        Args:
            user_interactions: 用户交互历史
            
        Returns:
            768维向量
        """
        # TODO: 实际用户向量生成
        # 方法1: 用户交互物品的向量加权平均
        # 方法2: 训练用户塔模型
        # 方法3: 基于协同过滤的隐向量
        
        # 示例：随机向量
        np.random.seed(len(user_interactions))
        embedding = np.random.randn(768).tolist()
        
        # 归一化
        norm = np.linalg.norm(embedding)
        embedding = [x / norm for x in embedding]
        
        return embedding

