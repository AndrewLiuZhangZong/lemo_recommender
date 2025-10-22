"""
排序器基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple


class Ranker(ABC):
    """排序器抽象基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def rank(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        item_ids: List[str],
        features: Dict[str, Any] = None
    ) -> List[Tuple[str, float]]:
        """
        对物品列表进行排序打分
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            user_id: 用户ID
            item_ids: 物品ID列表
            features: 额外特征
            
        Returns:
            (item_id, score)元组列表，按分数降序
        """
        pass

