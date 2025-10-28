"""
配置模板管理服务
"""
import logging
from typing import List, Optional, tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.template import Template, TemplateCreate, TemplateUpdate
from app.models.common import PaginationParams

logger = logging.getLogger(__name__)


class TemplateService:
    """配置模板服务"""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    async def create_template(
        self,
        data: TemplateCreate
    ) -> Template:
        """创建模板"""
        
        # 检查模板ID是否已存在
        existing = await self.collection.find_one({"template_id": data.template_id})
        if existing:
            raise ValueError(f"模板ID已存在: {data.template_id}")
        
        # 构建文档
        template_dict = {
            **data.model_dump(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.collection.insert_one(template_dict)
        template_dict["_id"] = result.inserted_id
        
        return Template.model_validate(template_dict)
    
    async def get_template(
        self,
        template_id: str
    ) -> Optional[Template]:
        """获取模板详情"""
        
        doc = await self.collection.find_one({"template_id": template_id})
        
        if doc:
            return Template.model_validate(doc)
        return None
    
    async def list_templates(
        self,
        scenario_type: Optional[str] = None,
        is_system: Optional[bool] = None,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[Template], int]:
        """查询模板列表"""
        
        # 构建查询条件
        query = {}
        if scenario_type:
            query["scenario_types"] = scenario_type
        if is_system is not None:
            query["is_system"] = is_system
        
        logger.info(f"查询模板列表: query={query}, pagination={pagination}")
        
        # 总数
        total = await self.collection.count_documents(query)
        logger.info(f"符合条件的总数: {total}")
        
        # 分页查询
        cursor = self.collection.find(query).sort("created_at", -1)
        
        if pagination:
            cursor = cursor.skip(pagination.skip).limit(pagination.page_size)
        
        templates = []
        async for doc in cursor:
            try:
                templates.append(Template.model_validate(doc))
            except Exception as e:
                logger.error(f"转换模板数据失败: {e}, doc={doc}")
                continue
        
        logger.info(f"实际返回 {len(templates)} 条数据")
        return templates, total
    
    async def update_template(
        self,
        template_id: str,
        data: TemplateUpdate
    ) -> Optional[Template]:
        """更新模板"""
        
        # 构建更新字段
        update_data = {
            k: v for k, v in data.model_dump(exclude_unset=True).items()
            if v is not None
        }
        
        if not update_data:
            return await self.get_template(template_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        # 执行更新
        result = await self.collection.find_one_and_update(
            {"template_id": template_id},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            return Template.model_validate(result)
        return None
    
    async def delete_template(
        self,
        template_id: str
    ) -> bool:
        """删除模板"""
        
        # 不允许删除系统模板
        template = await self.get_template(template_id)
        if template and template.is_system:
            raise ValueError("不能删除系统预设模板")
        
        result = await self.collection.delete_one({"template_id": template_id})
        return result.deleted_count > 0
    
    async def get_template_by_scenario_type(
        self,
        scenario_type: str
    ) -> Optional[Template]:
        """根据场景类型获取推荐模板（优先返回系统模板）"""
        
        # 先查询系统模板
        doc = await self.collection.find_one({
            "scenario_types": scenario_type,
            "is_system": True
        })
        
        if doc:
            return Template.model_validate(doc)
        
        # 没有系统模板，返回第一个匹配的自定义模板
        doc = await self.collection.find_one({
            "scenario_types": scenario_type
        })
        
        if doc:
            return Template.model_validate(doc)
        
        return None
    
    async def init_system_templates(self):
        """初始化系统预设模板"""
        
        # 检查是否已初始化
        count = await self.collection.count_documents({"is_system": True})
        if count > 0:
            logger.info(f"系统模板已存在 {count} 个，跳过初始化")
            return
        
        logger.info("开始初始化系统模板...")
        
        system_templates = [
            {
                "template_id": "ecommerce_default",
                "name": "电商推荐",
                "description": "适用于商品推荐场景，关注转化率和个性化",
                "scenario_types": ["ecommerce"],
                "config": {
                    "features": {
                        "item_features": [
                            {"name": "price", "type": "numeric", "weight": 1.2, "required": True},
                            {"name": "category", "type": "categorical", "weight": 1.5, "required": True},
                            {"name": "brand", "type": "categorical", "weight": 1.0, "required": False},
                        ],
                        "user_features": [
                            {"name": "age", "type": "numeric", "weight": 0.8, "required": False},
                            {"name": "gender", "type": "categorical", "weight": 0.6, "required": False},
                        ],
                        "context_features": [],
                    },
                    "recall": {
                        "strategies": [
                            {"name": "user_cf", "weight": 0.3, "limit": 100},
                            {"name": "item_cf", "weight": 0.3, "limit": 100},
                            {"name": "hot_items", "weight": 0.2, "limit": 50},
                        ],
                        "total_recall_limit": 500,
                        "dedup_strategy": "item_id",
                    },
                    "rank": {
                        "model": "deepfm",
                        "version": "v1.0",
                        "objective": "conversion_rate",
                    },
                    "rerank": {
                        "rules": [
                            {"name": "diversity", "weight": 0.3},
                        ],
                    },
                    "business_rules": {},
                },
                "is_system": True,
                "creator": "system",
            },
            {
                "template_id": "vlog_default",
                "name": "短视频推荐",
                "description": "适用于短视频feed流推荐，关注观看时长和完播率",
                "scenario_types": ["vlog"],
                "config": {
                    "features": {
                        "item_features": [
                            {"name": "duration", "type": "numeric", "weight": 1.0, "required": True},
                            {"name": "category", "type": "categorical", "weight": 1.5, "required": True},
                            {"name": "author_id", "type": "categorical", "weight": 1.2, "required": True},
                        ],
                        "user_features": [
                            {"name": "age", "type": "numeric", "weight": 0.6, "required": False},
                        ],
                        "context_features": [],
                    },
                    "recall": {
                        "strategies": [
                            {"name": "user_cf", "weight": 0.3, "limit": 150},
                            {"name": "hot_items", "weight": 0.3, "limit": 100},
                            {"name": "vector_search", "weight": 0.25, "limit": 100},
                        ],
                        "total_recall_limit": 600,
                        "dedup_strategy": "item_id",
                    },
                    "rank": {
                        "model": "wide_deep",
                        "version": "v1.0",
                        "objective": "watch_time",
                    },
                    "rerank": {
                        "rules": [
                            {"name": "diversity", "weight": 0.4},
                            {"name": "freshness", "weight": 0.3},
                        ],
                    },
                    "business_rules": {},
                },
                "is_system": True,
                "creator": "system",
            },
            {
                "template_id": "news_default",
                "name": "新闻推荐",
                "description": "适用于新闻资讯推荐，关注点击率和实时性",
                "scenario_types": ["news"],
                "config": {
                    "features": {
                        "item_features": [
                            {"name": "title", "type": "text", "weight": 1.5, "required": True},
                            {"name": "category", "type": "categorical", "weight": 1.5, "required": True},
                        ],
                        "user_features": [],
                        "context_features": [],
                    },
                    "recall": {
                        "strategies": [
                            {"name": "hot_items", "weight": 0.35, "limit": 100},
                            {"name": "user_cf", "weight": 0.25, "limit": 100},
                        ],
                        "total_recall_limit": 500,
                        "dedup_strategy": "item_id",
                    },
                    "rank": {
                        "model": "lightgbm",
                        "version": "v1.0",
                        "objective": "click_rate",
                    },
                    "rerank": {
                        "rules": [
                            {"name": "freshness", "weight": 0.4},
                            {"name": "diversity", "weight": 0.35},
                        ],
                    },
                    "business_rules": {},
                },
                "is_system": True,
                "creator": "system",
            },
            {
                "template_id": "music_default",
                "name": "音乐推荐",
                "description": "适用于音乐推荐场景，关注完播率和用户喜好",
                "scenario_types": ["music"],
                "config": {
                    "features": {
                        "item_features": [
                            {"name": "artist", "type": "categorical", "weight": 1.5, "required": True},
                            {"name": "genre", "type": "multi_categorical", "weight": 1.5, "required": True},
                        ],
                        "user_features": [],
                        "context_features": [],
                    },
                    "recall": {
                        "strategies": [
                            {"name": "user_cf", "weight": 0.35, "limit": 150},
                            {"name": "artist_match", "weight": 0.25, "limit": 100},
                        ],
                        "total_recall_limit": 500,
                        "dedup_strategy": "item_id",
                    },
                    "rank": {
                        "model": "deepfm",
                        "version": "v1.0",
                        "objective": "completion_rate",
                    },
                    "rerank": {
                        "rules": [
                            {"name": "diversity", "weight": 0.4},
                        ],
                    },
                    "business_rules": {},
                },
                "is_system": True,
                "creator": "system",
            },
            {
                "template_id": "content_default",
                "name": "内容推荐",
                "description": "通用内容推荐模板，适用于文章、帖子等场景",
                "scenario_types": ["content", "social", "personalized"],
                "config": {
                    "features": {
                        "item_features": [
                            {"name": "title", "type": "text", "weight": 1.2, "required": True},
                            {"name": "category", "type": "categorical", "weight": 1.3, "required": True},
                        ],
                        "user_features": [],
                        "context_features": [],
                    },
                    "recall": {
                        "strategies": [
                            {"name": "user_cf", "weight": 0.4, "limit": 150},
                            {"name": "hot_items", "weight": 0.3, "limit": 100},
                        ],
                        "total_recall_limit": 500,
                        "dedup_strategy": "item_id",
                    },
                    "rank": {
                        "model": "lightgbm",
                        "version": "v1.0",
                        "objective": "click_rate",
                    },
                    "rerank": {
                        "rules": [
                            {"name": "diversity", "weight": 0.5},
                        ],
                    },
                    "business_rules": {},
                },
                "is_system": True,
                "creator": "system",
            },
        ]
        
        # 插入系统模板
        for template_data in system_templates:
            template_data["created_at"] = datetime.utcnow()
            template_data["updated_at"] = datetime.utcnow()
            
            try:
                await self.collection.insert_one(template_data)
                logger.info(f"初始化系统模板: {template_data['template_id']}")
            except Exception as e:
                logger.error(f"初始化模板失败: {template_data['template_id']}, 错误: {e}")
        
        logger.info("系统模板初始化完成")

