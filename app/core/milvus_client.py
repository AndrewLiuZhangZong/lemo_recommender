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
        try:
            from pymilvus import connections
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
                timeout=10
            )
            self.connection = connections
            print(f"[Milvus] 已连接到 {self.host}:{self.port}")
        except ImportError:
            print("[Milvus] pymilvus未安装，使用模拟模式")
            self.enabled = False
        except Exception as e:
            print(f"[Milvus] 连接失败: {e}")
            self.enabled = False
    
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
            print(f"[Milvus模拟] 创建集合: {collection_name}, 维度: {dimension}")
            return False
        
        try:
            from pymilvus import Collection, CollectionSchema, FieldSchema, DataType, utility
            
            # 检查集合是否已存在
            if utility.has_collection(collection_name):
                print(f"[Milvus] 集合已存在: {collection_name}")
                return True
            
            # 定义字段
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="scenario_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="item_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension)
            ]
            
            schema = CollectionSchema(fields=fields, description=description)
            collection = Collection(name=collection_name, schema=schema)
            
            # 创建IVF_FLAT索引（适合中小规模数据）
            index_params = {
                "metric_type": "IP",  # Inner Product (余弦相似度)
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            
            # 加载到内存
            collection.load()
            
            print(f"[Milvus] 创建集合成功: {collection_name}, 维度: {dimension}")
            return True
            
        except Exception as e:
            print(f"[Milvus] 创建集合失败: {e}")
            return False
    
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
        if not item_ids:
            return 0
            
        if not self.enabled:
            print(f"[Milvus模拟] 插入 {len(item_ids)} 个向量到 {collection_name}")
            return len(item_ids)
        
        try:
            from pymilvus import Collection
            
            collection = Collection(collection_name)
            
            # 准备数据（按字段顺序）
            entities = [
                [tenant_id] * len(item_ids),    # tenant_id
                [scenario_id] * len(item_ids),  # scenario_id
                item_ids,                       # item_id
                embeddings                      # embedding
            ]
            
            # 插入数据
            result = collection.insert(entities)
            collection.flush()
            
            print(f"[Milvus] 插入成功: {len(item_ids)} 个向量到 {collection_name}")
            return len(item_ids)
            
        except Exception as e:
            print(f"[Milvus] 插入失败: {e}")
            return 0
    
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
            print(f"[Milvus模拟] 搜索相似向量: {collection_name}, Top {top_k}")
            # 返回模拟数据
            return [
                {"item_id": f"item_{i}", "score": 0.9 - i * 0.01}
                for i in range(min(top_k, 10))
            ]
        
        try:
            from pymilvus import Collection
            
            collection = Collection(collection_name)
            
            # 构建搜索表达式（租户+场景隔离）
            expr = f'tenant_id == "{tenant_id}" && scenario_id == "{scenario_id}"'
            if filters:
                for key, value in filters.items():
                    if isinstance(value, str):
                        expr += f' && {key} == "{value}"'
                    else:
                        expr += f' && {key} == {value}'
            
            # 搜索参数
            search_params = {
                "metric_type": "IP",
                "params": {"nprobe": 10}
            }
            
            # 执行搜索
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["item_id"]
            )
            
            # 格式化结果
            similar_items = []
            for hits in results:
                for hit in hits:
                    similar_items.append({
                        "item_id": hit.entity.get("item_id"),
                        "score": float(hit.score)
                    })
            
            print(f"[Milvus] 搜索成功: {collection_name}, 返回 {len(similar_items)} 个结果")
            return similar_items
            
        except Exception as e:
            print(f"[Milvus] 搜索失败: {e}")
            return []
    
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
        if not item_ids:
            return 0
            
        if not self.enabled:
            print(f"[Milvus模拟] 删除 {len(item_ids)} 个向量从 {collection_name}")
            return len(item_ids)
        
        try:
            from pymilvus import Collection
            
            collection = Collection(collection_name)
            
            # 构建删除表达式
            item_ids_str = '", "'.join(item_ids)
            expr = f'item_id in ["{item_ids_str}"]'
            
            collection.delete(expr)
            collection.flush()
            
            print(f"[Milvus] 删除成功: {len(item_ids)} 个向量从 {collection_name}")
            return len(item_ids)
            
        except Exception as e:
            print(f"[Milvus] 删除失败: {e}")
            return 0
    
    def close(self):
        """关闭连接"""
        if self.enabled and self.connection:
            try:
                self.connection.disconnect("default")
                print("[Milvus] 已断开连接")
            except Exception as e:
                print(f"[Milvus] 断开连接失败: {e}")


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
        # 方法1: 使用预训练模型（需要安装sentence-transformers）
        try:
            from sentence_transformers import SentenceTransformer
            
            # 提取文本特征
            text_parts = []
            if 'title' in item_metadata:
                text_parts.append(str(item_metadata['title']))
            if 'description' in item_metadata:
                text_parts.append(str(item_metadata['description']))
            if 'tags' in item_metadata:
                tags = item_metadata['tags']
                if isinstance(tags, list):
                    text_parts.extend(tags)
            
            text = ' '.join(text_parts)
            
            if text:
                model = SentenceTransformer('all-MiniLM-L6-v2')  # 384维
                embedding = model.encode(text, normalize_embeddings=True)
                # 填充到768维
                padded = np.pad(embedding, (0, 768 - len(embedding)), mode='constant')
                return padded.tolist()
        except ImportError:
            pass
        
        # 方法2: 降级到TF-IDF + 哈希（示例）
        # 基于metadata生成确定性向量
        np.random.seed(hash(str(sorted(item_metadata.items()))) % 2**32)
        embedding = np.random.randn(768)
        
        # 归一化
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    @staticmethod
    def generate_user_embedding(user_interactions: List[Dict[str, Any]]) -> List[float]:
        """
        生成用户向量（基于历史交互）
        
        Args:
            user_interactions: 用户交互历史 [{"item_id": "xxx", "action_type": "click", "item_embedding": [...]}]
            
        Returns:
            768维向量
        """
        if not user_interactions:
            # 冷启动：返回零向量
            return [0.0] * 768
        
        # 方法1: 用户交互物品的向量加权平均（基于行为类型权重）
        action_weights = {
            'view': 1.0,
            'click': 2.0,
            'like': 3.0,
            'share': 4.0,
            'purchase': 5.0,
            'finish': 3.0
        }
        
        weighted_sum = np.zeros(768)
        total_weight = 0.0
        
        for interaction in user_interactions[-100:]:  # 只取最近100个
            action_type = interaction.get('action_type', 'view')
            weight = action_weights.get(action_type, 1.0)
            
            # 如果有物品向量
            if 'item_embedding' in interaction:
                item_vec = np.array(interaction['item_embedding'])
                if len(item_vec) == 768:
                    weighted_sum += item_vec * weight
                    total_weight += weight
        
        if total_weight > 0:
            # 加权平均
            user_embedding = weighted_sum / total_weight
            # 归一化
            user_embedding = user_embedding / np.linalg.norm(user_embedding)
            return user_embedding.tolist()
        
        # 方法2: 降级到基于行为模式的确定性向量
        np.random.seed(len(user_interactions) % 2**32)
        embedding = np.random.randn(768)
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()

