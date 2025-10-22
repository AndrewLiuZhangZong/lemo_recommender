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
            return Experiment(**doc)
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
        
        return [Experiment(**doc) for doc in docs]
    
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
            return {"sample_size": 0}
        
        # 获取这些用户的交互数据
        # TODO: 从interactions collection聚合计算指标
        
        # 简化：返回模拟数据
        metrics = {
            "sample_size": len(user_ids),
            "ctr": 0.05,
            "avg_watch_duration": 45.2,
            "engagement_rate": 0.12
        }
        
        return metrics
    
    def _significance_test(
        self,
        control_metrics: Dict[str, float],
        treatment_metrics: Dict[str, float],
        metric_name: str
    ) -> tuple[bool, float]:
        """
        统计显著性检验（简化版）
        
        Returns:
            (是否显著, p值)
        """
        # TODO: 实现真实的统计检验（T检验、Z检验等）
        
        # 简化：基于样本量和差异判断
        control_value = control_metrics.get(metric_name, 0)
        treatment_value = treatment_metrics.get(metric_name, 0)
        
        diff = abs(treatment_value - control_value)
        
        # 模拟p值
        if diff > 0.01:
            return True, 0.02
        else:
            return False, 0.15

