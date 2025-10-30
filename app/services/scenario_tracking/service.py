"""
场景埋点配置管理服务

职责：
1. 管理场景埋点配置（CRUD）
2. 提供场景模板
3. 配置验证
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging

from app.models.scenario_tracking import (
    ScenarioTrackingConfig,
    ScenarioTrackingTemplate,
    FieldValidation,
    ScenarioType,
    BUILT_IN_TEMPLATES
)

logger = logging.getLogger(__name__)


class ScenarioTrackingService:
    """场景埋点配置服务"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        初始化服务
        
        Args:
            db: MongoDB数据库实例
        """
        self.db = db
        self.configs_collection = db.scenario_tracking_configs
        self.templates_collection = db.scenario_tracking_templates
    
    async def create_config(
        self,
        tenant_id: str,
        scenario_id: str,
        scenario_type: str,
        name: str,
        required_fields: List[Dict[str, Any]],
        optional_fields: Optional[List[Dict[str, Any]]] = None,
        recommended_actions: Optional[List[str]] = None,
        description: str = "",
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建场景埋点配置
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            scenario_type: 场景类型
            name: 配置名称
            required_fields: 必填字段列表
            optional_fields: 可选字段列表
            recommended_actions: 推荐的行为类型
            description: 描述
            created_by: 创建人
        
        Returns:
            创建的配置
        """
        # 检查是否已存在
        existing = await self.configs_collection.find_one({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id
        })
        
        if existing:
            raise ValueError(
                f"Tracking config already exists for tenant {tenant_id}, "
                f"scenario {scenario_id}"
            )
        
        # 构建配置对象
        config_data = {
            "config_id": ObjectId().hex,
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "scenario_type": scenario_type,
            "name": name,
            "description": description,
            "required_fields": required_fields,
            "optional_fields": optional_fields or [],
            "recommended_actions": recommended_actions or [],
            "is_active": True,
            "version": "1.0",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "created_by": created_by
        }
        
        # 验证配置
        config = ScenarioTrackingConfig.model_validate(config_data)
        
        # 保存到数据库
        await self.configs_collection.insert_one(config.model_dump())
        
        logger.info(
            f"Created tracking config: {tenant_id}/{scenario_id} ({scenario_type})"
        )
        
        return config.model_dump()
    
    async def get_config(
        self,
        tenant_id: str,
        scenario_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取场景埋点配置
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
        
        Returns:
            配置字典，不存在返回None
        """
        config = await self.configs_collection.find_one({
            "tenant_id": tenant_id,
            "scenario_id": scenario_id,
            "is_active": True
        })
        
        if not config:
            return None
        
        # 移除MongoDB的_id字段
        if '_id' in config:
            del config['_id']
        
        return config
    
    async def list_configs(
        self,
        tenant_id: Optional[str] = None,
        scenario_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        列出场景埋点配置
        
        Args:
            tenant_id: 租户ID（可选）
            scenario_type: 场景类型（可选）
            is_active: 是否启用（可选）
            skip: 跳过数量
            limit: 返回数量
        
        Returns:
            {
                "configs": List[dict],
                "total": int,
                "skip": int,
                "limit": int
            }
        """
        # 构建查询条件
        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id
        if scenario_type:
            query["scenario_type"] = scenario_type
        if is_active is not None:
            query["is_active"] = is_active
        
        # 查询总数
        total = await self.configs_collection.count_documents(query)
        
        # 查询列表
        cursor = self.configs_collection.find(query).skip(skip).limit(limit)
        configs = await cursor.to_list(length=limit)
        
        # 移除_id字段
        for config in configs:
            if '_id' in config:
                del config['_id']
        
        return {
            "configs": configs,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    async def update_config(
        self,
        tenant_id: str,
        scenario_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新场景埋点配置
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            updates: 更新字段
        
        Returns:
            更新后的配置
        """
        # 禁止更新的字段
        forbidden_fields = ["config_id", "tenant_id", "scenario_id", "created_at"]
        for field in forbidden_fields:
            if field in updates:
                del updates[field]
        
        # 添加更新时间
        updates["updated_at"] = datetime.now()
        
        # 更新数据库
        result = await self.configs_collection.find_one_and_update(
            {"tenant_id": tenant_id, "scenario_id": scenario_id},
            {"$set": updates},
            return_document=True
        )
        
        if not result:
            raise ValueError(
                f"Tracking config not found: {tenant_id}/{scenario_id}"
            )
        
        # 移除_id
        if '_id' in result:
            del result['_id']
        
        logger.info(f"Updated tracking config: {tenant_id}/{scenario_id}")
        
        return result
    
    async def delete_config(
        self,
        tenant_id: str,
        scenario_id: str
    ) -> bool:
        """
        删除场景埋点配置（软删除）
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
        
        Returns:
            是否删除成功
        """
        result = await self.configs_collection.update_one(
            {"tenant_id": tenant_id, "scenario_id": scenario_id},
            {"$set": {"is_active": False, "updated_at": datetime.now()}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Deleted tracking config: {tenant_id}/{scenario_id}")
            return True
        
        return False
    
    async def create_from_template(
        self,
        tenant_id: str,
        scenario_id: str,
        template_id: str,
        name: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从模板创建配置
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            template_id: 模板ID
            name: 配置名称（可选，默认使用模板名称）
            created_by: 创建人
        
        Returns:
            创建的配置
        """
        # 查找模板
        template = await self.get_template(template_id)
        
        if not template:
            # 尝试从内置模板获取
            if template_id in BUILT_IN_TEMPLATES:
                template = BUILT_IN_TEMPLATES[template_id]
            else:
                raise ValueError(f"Template not found: {template_id}")
        
        # 从模板创建配置
        config = template.get("config", {})
        
        return await self.create_config(
            tenant_id=tenant_id,
            scenario_id=scenario_id,
            scenario_type=template.get("scenario_type", "custom"),
            name=name or template.get("name", "未命名配置"),
            required_fields=config.get("required_fields", []),
            optional_fields=config.get("optional_fields", []),
            recommended_actions=config.get("recommended_actions", []),
            description=template.get("description", ""),
            created_by=created_by
        )
    
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        获取模板
        
        Args:
            template_id: 模板ID
        
        Returns:
            模板字典，不存在返回None
        """
        # 先从数据库查找
        template = await self.templates_collection.find_one({
            "template_id": template_id
        })
        
        if template:
            if '_id' in template:
                del template['_id']
            return template
        
        # 从内置模板查找
        return BUILT_IN_TEMPLATES.get(template_id)
    
    async def list_templates(
        self,
        scenario_type: Optional[str] = None,
        is_official: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        列出模板
        
        Args:
            scenario_type: 场景类型（可选）
            is_official: 是否官方模板（可选）
        
        Returns:
            模板列表
        """
        # 从数据库查询
        query = {}
        if scenario_type:
            query["scenario_type"] = scenario_type
        if is_official is not None:
            query["is_official"] = is_official
        
        cursor = self.templates_collection.find(query)
        db_templates = await cursor.to_list(length=1000)
        
        # 移除_id
        for template in db_templates:
            if '_id' in template:
                del template['_id']
        
        # 合并内置模板
        built_in = []
        for template_id, template in BUILT_IN_TEMPLATES.items():
            if scenario_type and template.get("scenario_type") != scenario_type:
                continue
            built_in.append(template)
        
        return built_in + db_templates
    
    def get_built_in_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有内置模板
        
        Returns:
            内置模板字典
        """
        return BUILT_IN_TEMPLATES

