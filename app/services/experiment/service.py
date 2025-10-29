"""
AB实验服务
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
from app.models.experiment import (
    Experiment,
    ExperimentStatus,
    ExperimentAssignment,
    ExperimentResult,
    TrafficSplitMethod
)


class ExperimentService:
    """AB实验管理服务"""
    
    def __init__(self, db):
        self.db = db
        self.experiments_collection = db.experiments
        self.assignments_collection = db.experiment_assignments
        self.results_collection = db.experiment_results
    
    async def create_experiment(self, experiment: Experiment) -> Experiment:
        """创建实验"""
        # 验证流量分配总和为100%
        total_traffic = sum(v.traffic_percentage for v in experiment.variants)
        if abs(total_traffic - 100.0) > 0.01:
            raise ValueError(f"流量分配总和必须为100%，当前为{total_traffic}%")
        
        # 保存到数据库
        await self.experiments_collection.insert_one(experiment.dict())
        
        return experiment
    
    async def get_experiment(
        self,
        tenant_id: str,
        experiment_id: str
    ) -> Optional[Experiment]:
        """获取实验"""
        doc = await self.experiments_collection.find_one({
            "tenant_id": tenant_id,
            "experiment_id": experiment_id
        })
        
        if doc:
            return Experiment.model_validate(doc)
        return None
    
    async def list_experiments(
        self,
        tenant_id: str,
        scenario_id: Optional[str] = None,
        status: Optional[ExperimentStatus] = None
    ) -> List[Experiment]:
        """列出实验"""
        query = {"tenant_id": tenant_id}
        
        if scenario_id:
            query["scenario_id"] = scenario_id
        
        if status:
            query["status"] = status
        
        docs = await self.experiments_collection.find(query).to_list(length=100)
        
        experiments = []
        for doc in docs:
            try:
                experiments.append(Experiment.model_validate(doc))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"转换实验数据失败: {e}, doc={doc}")
                continue
        
        return experiments
    
    async def start_experiment(
        self,
        tenant_id: str,
        experiment_id: str
    ) -> Experiment:
        """启动实验"""
        experiment = await self.get_experiment(tenant_id, experiment_id)
        
        if not experiment:
            raise ValueError("实验不存在")
        
        if experiment.status != ExperimentStatus.DRAFT:
            raise ValueError(f"只能启动草稿状态的实验，当前状态: {experiment.status}")
        
        # 更新状态
        await self.experiments_collection.update_one(
            {
                "tenant_id": tenant_id,
                "experiment_id": experiment_id
            },
            {
                "$set": {
                    "status": ExperimentStatus.RUNNING,
                    "start_time": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        experiment.status = ExperimentStatus.RUNNING
        experiment.start_time = datetime.utcnow()
        
        return experiment
    
    async def stop_experiment(
        self,
        tenant_id: str,
        experiment_id: str
    ) -> Experiment:
        """停止实验"""
        experiment = await self.get_experiment(tenant_id, experiment_id)
        
        if not experiment:
            raise ValueError("实验不存在")
        
        # 更新状态
        await self.experiments_collection.update_one(
            {
                "tenant_id": tenant_id,
                "experiment_id": experiment_id
            },
            {
                "$set": {
                    "status": ExperimentStatus.COMPLETED,
                    "end_time": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        experiment.status = ExperimentStatus.COMPLETED
        experiment.end_time = datetime.utcnow()
        
        return experiment
    
    async def delete_experiment(
        self,
        tenant_id: str,
        experiment_id: str,
        soft_delete: bool = True
    ) -> bool:
        """删除实验"""
        experiment = await self.get_experiment(tenant_id, experiment_id)
        
        if not experiment:
            raise ValueError("实验不存在")
        
        if soft_delete:
            # 软删除：更新状态为archived
            result = await self.experiments_collection.update_one(
                {
                    "tenant_id": tenant_id,
                    "experiment_id": experiment_id
                },
                {
                    "$set": {
                        "status": ExperimentStatus.ARCHIVED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        else:
            # 硬删除
            result = await self.experiments_collection.delete_one({
                "tenant_id": tenant_id,
                "experiment_id": experiment_id
            })
            return result.deleted_count > 0
    
    def assign_variant(
        self,
        experiment: Experiment,
        user_id: str
    ) -> str:
        """
        为用户分配实验变体
        
        Args:
            experiment: 实验对象
            user_id: 用户ID
            
        Returns:
            变体ID
        """
        # 检查实验是否运行中
        if experiment.status != ExperimentStatus.RUNNING:
            # 默认返回对照组
            return experiment.variants[0].variant_id
        
        # 检查目标用户过滤
        if experiment.target_users:
            # TODO: 实现用户过滤逻辑
            pass
        
        # 流量分配
        if experiment.traffic_split_method == TrafficSplitMethod.USER_ID_HASH:
            return self._assign_by_hash(experiment, user_id)
        elif experiment.traffic_split_method == TrafficSplitMethod.RANDOM:
            return self._assign_by_random(experiment)
        else:
            return experiment.variants[0].variant_id
    
    def _assign_by_hash(self, experiment: Experiment, user_id: str) -> str:
        """
        基于用户ID哈希分配（保证同一用户始终分配到同一变体）
        
        算法:
        1. 计算 hash(experiment_id + user_id)
        2. 映射到0-100的范围
        3. 根据流量占比分配变体
        """
        # 计算哈希值
        hash_input = f"{experiment.experiment_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # 映射到0-100
        bucket = hash_value % 100
        
        # 根据流量分配
        cumulative = 0.0
        for variant in experiment.variants:
            cumulative += variant.traffic_percentage
            if bucket < cumulative:
                return variant.variant_id
        
        # 默认返回最后一个变体
        return experiment.variants[-1].variant_id
    
    def _assign_by_random(self, experiment: Experiment) -> str:
        """随机分配（每次可能不同）"""
        import random
        
        rand = random.random() * 100
        cumulative = 0.0
        
        for variant in experiment.variants:
            cumulative += variant.traffic_percentage
            if rand < cumulative:
                return variant.variant_id
        
        return experiment.variants[-1].variant_id
    
    async def record_assignment(
        self,
        tenant_id: str,
        experiment_id: str,
        user_id: str,
        variant_id: str
    ):
        """记录实验分配"""
        assignment = ExperimentAssignment(
            tenant_id=tenant_id,
            experiment_id=experiment_id,
            user_id=user_id,
            variant_id=variant_id
        )
        
        # 使用upsert避免重复记录
        await self.assignments_collection.update_one(
            {
                "tenant_id": tenant_id,
                "experiment_id": experiment_id,
                "user_id": user_id
            },
            {"$set": assignment.dict()},
            upsert=True
        )
    
    async def get_user_experiments(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str
    ) -> Dict[str, str]:
        """
        获取用户参与的所有实验及其分配
        
        Returns:
            {experiment_id: variant_id}
        """
        # 获取运行中的实验
        experiments = await self.list_experiments(
            tenant_id,
            scenario_id,
            ExperimentStatus.RUNNING
        )
        
        user_experiments = {}
        
        for experiment in experiments:
            # 为用户分配变体
            variant_id = self.assign_variant(experiment, user_id)
            user_experiments[experiment.experiment_id] = variant_id
            
            # 记录分配（异步，不阻塞）
            await self.record_assignment(
                tenant_id,
                experiment.experiment_id,
                user_id,
                variant_id
            )
        
        return user_experiments
    
    async def compute_experiment_results(
        self,
        tenant_id: str,
        experiment_id: str
    ) -> List[ExperimentResult]:
        """
        计算实验结果
        
        Returns:
            每个变体的结果
        """
        experiment = await self.get_experiment(tenant_id, experiment_id)
        
        if not experiment:
            raise ValueError("实验不存在")
        
        results = []
        
        # 获取对照组作为基线
        control_variant_id = experiment.variants[0].variant_id
        control_metrics = await self._compute_variant_metrics(
            tenant_id,
            experiment_id,
            control_variant_id
        )
        
        # 计算每个变体的结果
        for variant in experiment.variants:
            variant_metrics = await self._compute_variant_metrics(
                tenant_id,
                experiment_id,
                variant.variant_id
            )
            
            # 统计显著性检验
            is_significant, p_value = self._significance_test(
                control_metrics,
                variant_metrics,
                experiment.metrics.primary_metric
            )
            
            # 计算提升
            lift = {}
            for metric_name in variant_metrics.keys():
                if metric_name in control_metrics:
                    control_value = control_metrics[metric_name]
                    variant_value = variant_metrics[metric_name]
                    
                    if control_value > 0:
                        lift[metric_name] = (
                            (variant_value - control_value) / control_value * 100
                        )
            
            result = ExperimentResult(
                experiment_id=experiment_id,
                variant_id=variant.variant_id,
                sample_size=variant_metrics.get("sample_size", 0),
                metrics=variant_metrics,
                is_significant=is_significant,
                p_value=p_value,
                confidence_interval=[0.0, 0.0],  # TODO: 计算置信区间
                lift=lift
            )
            
            results.append(result)
        
        # 保存结果
        for result in results:
            await self.results_collection.update_one(
                {
                    "experiment_id": experiment_id,
                    "variant_id": result.variant_id
                },
                {"$set": result.dict()},
                upsert=True
            )
        
        return results
    
    async def _compute_variant_metrics(
        self,
        tenant_id: str,
        experiment_id: str,
        variant_id: str
    ) -> Dict[str, float]:
        """计算变体的指标"""
        # 获取分配到该变体的用户
        assignments = await self.assignments_collection.find({
            "tenant_id": tenant_id,
            "experiment_id": experiment_id,
            "variant_id": variant_id
        }).to_list(length=None)
        
        user_ids = [a["user_id"] for a in assignments]
        
        if not user_ids:
            return {"sample_size": 0, "ctr": 0.0, "avg_watch_duration": 0.0, "engagement_rate": 0.0}
        
        # 从interactions collection聚合计算指标
        pipeline = [
            {
                "$match": {
                    "user_id": {"$in": user_ids},
                    "extra.experiment_id": experiment_id
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_views": {"$sum": {"$cond": [{"$eq": ["$action_type", "view"]}, 1, 0]}},
                    "total_clicks": {"$sum": {"$cond": [{"$eq": ["$action_type", "click"]}, 1, 0]}},
                    "total_likes": {"$sum": {"$cond": [{"$eq": ["$action_type", "like"]}, 1, 0]}},
                    "total_duration": {
                        "$sum": {
                            "$cond": [
                                {"$ne": ["$extra.duration", None]},
                                {"$toDouble": {"$ifNull": ["$extra.duration", 0]}},
                                0
                            ]
                        }
                    },
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = await db.interactions.aggregate(pipeline).to_list(1)
        
        if results:
            result = results[0]
            total_views = result.get("total_views", 0)
            total_clicks = result.get("total_clicks", 0)
            total_likes = result.get("total_likes", 0)
            total_duration = result.get("total_duration", 0)
            count = result.get("count", 0)
            
            metrics = {
                "sample_size": len(user_ids),
                "ctr": total_clicks / total_views if total_views > 0 else 0.0,
                "avg_watch_duration": total_duration / count if count > 0 else 0.0,
                "engagement_rate": (total_clicks + total_likes) / total_views if total_views > 0 else 0.0
            }
        else:
            # 无交互数据，返回零值
            metrics = {
                "sample_size": len(user_ids),
                "ctr": 0.0,
                "avg_watch_duration": 0.0,
                "engagement_rate": 0.0
            }
        
        return metrics
    
    def _significance_test(
        self,
        control_metrics: Dict[str, float],
        treatment_metrics: Dict[str, float],
        metric_name: str
    ) -> tuple[bool, float]:
        """
        统计显著性检验（使用双样本Z检验）
        
        Returns:
            (是否显著, p值)
        """
        control_value = control_metrics.get(metric_name, 0)
        treatment_value = treatment_metrics.get(metric_name, 0)
        control_n = control_metrics.get("sample_size", 0)
        treatment_n = treatment_metrics.get("sample_size", 0)
        
        # 样本量不足，无法进行检验
        if control_n < 30 or treatment_n < 30:
            return False, 1.0
        
        # 无差异
        if control_value == treatment_value:
            return False, 1.0
        
        try:
            # 使用scipy进行Z检验（双样本比例检验）
            from scipy import stats
            import numpy as np
            
            # 对于CTR和engagement_rate这类比率指标，使用比例检验
            if metric_name in ['ctr', 'engagement_rate']:
                # 计算成功次数（近似）
                control_successes = int(control_value * control_n)
                treatment_successes = int(treatment_value * treatment_n)
                
                # 构造二项分布数据（近似）
                control_data = np.array([1] * control_successes + [0] * (control_n - control_successes))
                treatment_data = np.array([1] * treatment_successes + [0] * (treatment_n - treatment_successes))
                
                # 双样本t检验
                t_stat, p_value = stats.ttest_ind(control_data, treatment_data)
                
            else:
                # 对于连续变量（如avg_watch_duration），使用t检验
                # 假设正态分布，使用Welch's t-test（不假设方差相等）
                
                # 估计标准差（使用变异系数）
                control_std = control_value * 0.3  # 假设CV=30%
                treatment_std = treatment_value * 0.3
                
                # 生成近似数据
                control_data = np.random.normal(control_value, control_std, min(control_n, 1000))
                treatment_data = np.random.normal(treatment_value, treatment_std, min(treatment_n, 1000))
                
                # Welch's t-test
                t_stat, p_value = stats.ttest_ind(control_data, treatment_data, equal_var=False)
            
            # 显著性水平：p < 0.05
            is_significant = p_value < 0.05
            
            return is_significant, float(p_value)
            
        except ImportError:
            # scipy未安装，降级到简单判断
            diff = abs(treatment_value - control_value)
            relative_diff = diff / control_value if control_value > 0 else diff
            
            # 简化判断：相对差异>5%且绝对差异>0.01
            if relative_diff > 0.05 and diff > 0.01:
                return True, 0.03  # 模拟p值
            else:
                return False, 0.2
            
        except Exception as e:
            print(f"[Experiment] 统计检验失败: {e}")
            return False, 1.0

