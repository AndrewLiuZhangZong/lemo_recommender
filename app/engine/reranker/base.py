"""
重排器基类
"""
from abc import ABC, abstractmethod
from typing import List, Tuple


class Reranker(ABC):
    """重排器抽象基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def rerank(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        ranked_items: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        """
        重排已排序的物品列表
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            user_id: 用户ID
            ranked_items: 已排序的(item_id, score)列表
            
        Returns:
            重排后的(item_id, score)列表
        """
        pass

