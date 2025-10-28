"""
场景管理服务
"""
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from app.models.scenario import (
    Scenario,
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioStatus
)
from app.models.base import PaginationParams


class ScenarioService:
    """场景管理服务"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.scenarios
    
    async def create_scenario(
        self,
        tenant_id: str,
        data: ScenarioCreate
    ) -> Scenario:
        """创建场景"""
        
        # 检查scenario_id是否已存在
        existing = await self.collection.find_one({
            "tenant_id": tenant_id,
            "scenario_id": data.scenario_id
        })
        if existing:
            raise ValueError(f"场景ID已存在: {data.scenario_id}")
        
        # 创建场景文档
        scenario_dict = {
            "tenant_id": tenant_id,
            **data.model_dump(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.collection.insert_one(scenario_dict)
        scenario_dict["_id"] = result.inserted_id
        
        return Scenario.model_validate(scenario_dict)
    
    async def get_scenario(
        self,
        tenant_id: str,
        scenario_id: str
    ) -> Optional[Scenario]:
        """获取场景详情"""
        
        doc = await self.collection.find_one({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id
        })
        
        if doc:
            return Scenario.model_validate(doc)
        return None
    
    async def list_scenarios(
        self,
        tenant_id: str,
        status: Optional[ScenarioStatus] = None,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[Scenario], int]:
        """查询场景列表"""
        import logging
        logger = logging.getLogger(__name__)
        
        # 构建查询条件
        query = {}
        # 如果 tenant_id 不为空，则添加租户过滤
        if tenant_id and tenant_id.strip():
            query["tenant_id"] = tenant_id
        if status:
            query["status"] = status
        
        logger.info(f"查询场景列表: query={query}, pagination={pagination}")
        
        # 总数
        total = await self.collection.count_documents(query)
        logger.info(f"符合条件的总数: {total}")
        
        # 分页查询
        cursor = self.collection.find(query).sort("created_at", -1)
        
        if pagination:
            cursor = cursor.skip(pagination.skip).limit(pagination.page_size)
        
        scenarios = []
        async for doc in cursor:
            logger.debug(f"查询到文档: scenario_id={doc.get('scenario_id')}, tenant_id={doc.get('tenant_id')}")
            try:
                # 将 MongoDB 文档转换为 Pydantic 模型
                # Pydantic 会自动处理类型转换和默认值
                scenario = Scenario.model_validate(doc)
                scenarios.append(scenario)
            except Exception as e:
                logger.error(f"转换场景数据失败: {e}, doc={doc}")
                # 跳过无法转换的数据
                continue
        
        logger.info(f"实际返回 {len(scenarios)} 条数据")
        return scenarios, total
    
    async def update_scenario(
        self,
        tenant_id: str,
        scenario_id: str,
        data: ScenarioUpdate
    ) -> Optional[Scenario]:
        """更新场景"""
        
        # 构建更新字段
        update_data = {
            k: v for k, v in data.model_dump(exclude_unset=True).items()
            if v is not None
        }
        
        if not update_data:
            return await self.get_scenario(tenant_id, scenario_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        # 执行更新
        result = await self.collection.find_one_and_update(
            {"tenant_id": tenant_id, "scenario_id": scenario_id},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            return Scenario.model_validate(result)
        return None
    
    async def delete_scenario(
        self,
        tenant_id: str,
        scenario_id: str
    ) -> bool:
        """删除场景"""
        
        result = await self.collection.delete_one({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id
        })
        
        return result.deleted_count > 0
    
    async def validate_scenario_config(
        self,
        tenant_id: str,
        scenario_id: str
    ) -> dict:
        """验证场景配置"""
        
        scenario = await self.get_scenario(tenant_id, scenario_id)
        if not scenario:
            raise ValueError(f"场景不存在: {scenario_id}")
        
        errors = []
        warnings = []
        
        # 验证召回策略
        recall_strategies = scenario.config.recall.get("strategies", [])
        if not recall_strategies:
            errors.append("至少需要配置一个召回策略")
        
        total_weight = sum(s.get("weight", 0) for s in recall_strategies)
        if abs(total_weight - 1.0) > 0.01:
            warnings.append(f"召回策略权重之和应为1.0，当前为{total_weight}")
        
        # 验证排序模型
        rank_model = scenario.config.rank.model
        if rank_model not in ["lightgbm", "deepfm", "wide_deep", "xgboost"]:
            warnings.append(f"未知的排序模型: {rank_model}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

