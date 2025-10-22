"""
召回策略基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class RecallStrategy(ABC):
    """召回策略抽象基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def recall(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        limit: int = 100,
        params: Dict[str, Any] = None
    ) -> List[str]:
        """
        召回物品ID列表
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            user_id: 用户ID
            limit: 召回数量
            params: 额外参数
            
        Returns:
            物品ID列表
        """
        pass


class RecallResult:
    """召回结果"""
    
    def __init__(self, strategy_name: str, item_ids: List[str], weight: float = 1.0):
        self.strategy_name = strategy_name
        self.item_ids = item_ids
        self.weight = weight

