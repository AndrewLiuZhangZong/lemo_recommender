"""
实验效果分析
"""
from typing import Dict, Any, List
import numpy as np
from scipy import stats
from dataclasses import dataclass


@dataclass
class MetricStats:
    """指标统计"""
    mean: float
    std: float
    count: int
    confidence_interval: tuple[float, float]


class ExperimentAnalyzer:
    """实验效果分析器"""
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.z_score = stats.norm.ppf((1 + confidence_level) / 2)
    
    def compute_metric_stats(
        self,
        values: List[float]
    ) -> MetricStats:
        """
        计算指标统计量
        
        Args:
            values: 指标值列表
            
        Returns:
            统计结果
        """
        if not values:
            return MetricStats(0, 0, 0, (0, 0))
        
        arr = np.array(values)
        mean = np.mean(arr)
        std = np.std(arr, ddof=1)
        count = len(arr)
        
        # 置信区间
        se = std / np.sqrt(count)
        margin = self.z_score * se
        ci = (mean - margin, mean + margin)
        
        return MetricStats(
            mean=float(mean),
            std=float(std),
            count=count,
            confidence_interval=ci
        )
    
    def t_test(
        self,
        control_values: List[float],
        treatment_values: List[float]
    ) -> Dict[str, Any]:
        """
        T检验（独立样本T检验）
        
        用于比较两个变体在某个指标上的差异是否显著
        
        Args:
            control_values: 对照组数据
            treatment_values: 实验组数据
            
        Returns:
            检验结果 {
                "t_statistic": float,
                "p_value": float,
                "is_significant": bool,
                "control_mean": float,
                "treatment_mean": float,
                "lift": float
            }
        """
        if not control_values or not treatment_values:
            return {
                "t_statistic": 0,
                "p_value": 1.0,
                "is_significant": False,
                "control_mean": 0,
                "treatment_mean": 0,
                "lift": 0
            }
        
        control_arr = np.array(control_values)
        treatment_arr = np.array(treatment_values)
        
        # T检验
        t_stat, p_value = stats.ttest_ind(treatment_arr, control_arr)
        
        # 计算均值和提升
        control_mean = np.mean(control_arr)
        treatment_mean = np.mean(treatment_arr)
        
        lift = 0
        if control_mean != 0:
            lift = (treatment_mean - control_mean) / control_mean * 100
        
        # 判断显著性
        is_significant = p_value < (1 - self.confidence_level)
        
        return {
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "is_significant": is_significant,
            "control_mean": float(control_mean),
            "treatment_mean": float(treatment_mean),
            "lift": float(lift)
        }
    
    def proportion_z_test(
        self,
        control_success: int,
        control_total: int,
        treatment_success: int,
        treatment_total: int
    ) -> Dict[str, Any]:
        """
        比例Z检验（用于CTR、转化率等二元指标）
        
        Args:
            control_success: 对照组成功次数
            control_total: 对照组总次数
            treatment_success: 实验组成功次数
            treatment_total: 实验组总次数
            
        Returns:
            检验结果
        """
        if control_total == 0 or treatment_total == 0:
            return {
                "z_statistic": 0,
                "p_value": 1.0,
                "is_significant": False,
                "control_rate": 0,
                "treatment_rate": 0,
                "lift": 0
            }
        
        # 计算比例
        p1 = control_success / control_total
        p2 = treatment_success / treatment_total
        
        # 合并比例
        p_pooled = (control_success + treatment_success) / (control_total + treatment_total)
        
        # 标准误差
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/control_total + 1/treatment_total))
        
        # Z统计量
        z_stat = (p2 - p1) / se if se > 0 else 0
        
        # P值（双尾检验）
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        # 提升
        lift = 0
        if p1 != 0:
            lift = (p2 - p1) / p1 * 100
        
        # 判断显著性
        is_significant = p_value < (1 - self.confidence_level)
        
        return {
            "z_statistic": float(z_stat),
            "p_value": float(p_value),
            "is_significant": is_significant,
            "control_rate": float(p1),
            "treatment_rate": float(p2),
            "lift": float(lift),
            "confidence_interval": self._proportion_ci(p2, treatment_total)
        }
    
    def _proportion_ci(
        self,
        proportion: float,
        n: int
    ) -> tuple[float, float]:
        """计算比例的置信区间"""
        se = np.sqrt(proportion * (1 - proportion) / n)
        margin = self.z_score * se
        
        return (
            max(0, proportion - margin),
            min(1, proportion + margin)
        )
    
    def sample_size_calculator(
        self,
        baseline_rate: float,
        min_detectable_effect: float,
        alpha: float = 0.05,
        power: float = 0.8
    ) -> int:
        """
        样本量计算器
        
        Args:
            baseline_rate: 基线转化率（如0.05表示5%）
            min_detectable_effect: 最小可检测效应（相对提升，如0.1表示10%）
            alpha: 第一类错误概率（显著性水平）
            power: 统计功效（1 - 第二类错误概率）
            
        Returns:
            每组所需样本量
        """
        # Z分数
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)
        
        # 实验组预期转化率
        treatment_rate = baseline_rate * (1 + min_detectable_effect)
        
        # 样本量公式
        p_avg = (baseline_rate + treatment_rate) / 2
        
        numerator = (z_alpha + z_beta) ** 2 * 2 * p_avg * (1 - p_avg)
        denominator = (treatment_rate - baseline_rate) ** 2
        
        n = int(np.ceil(numerator / denominator))
        
        return n
    
    def sequential_test(
        self,
        control_stats: MetricStats,
        treatment_stats: MetricStats,
        spending_function: str = "obrien_fleming"
    ) -> Dict[str, Any]:
        """
        序贯检验（Sequential Testing）
        
        允许在实验过程中多次查看数据，同时控制第一类错误
        
        Args:
            control_stats: 对照组统计
            treatment_stats: 实验组统计
            spending_function: α消耗函数（obrien_fleming/pocock）
            
        Returns:
            检验结果
        """
        # TODO: 实现完整的序贯检验
        # 这里简化处理
        
        # 计算效应量
        pooled_std = np.sqrt(
            (control_stats.std ** 2 + treatment_stats.std ** 2) / 2
        )
        
        effect_size = 0
        if pooled_std > 0:
            effect_size = (treatment_stats.mean - control_stats.mean) / pooled_std
        
        # 简化的显著性判断
        is_significant = abs(effect_size) > 0.2  # Cohen's d > 0.2
        
        return {
            "effect_size": float(effect_size),
            "is_significant": is_significant,
            "can_stop_early": is_significant and control_stats.count > 1000
        }
    
    def multi_armed_bandit_thompson_sampling(
        self,
        variant_stats: Dict[str, tuple[int, int]]
    ) -> str:
        """
        多臂老虎机 - Thompson Sampling
        
        动态调整流量分配，倾向于表现更好的变体
        
        Args:
            variant_stats: 变体统计 {variant_id: (成功次数, 总次数)}
            
        Returns:
            建议分配的变体ID
        """
        samples = {}
        
        for variant_id, (success, total) in variant_stats.items():
            failure = total - success
            
            # Beta分布采样
            sample = np.random.beta(success + 1, failure + 1)
            samples[variant_id] = sample
        
        # 返回采样值最大的变体
        best_variant = max(samples.items(), key=lambda x: x[1])[0]
        
        return best_variant


# 使用示例
if __name__ == '__main__':
    analyzer = ExperimentAnalyzer(confidence_level=0.95)
    
    # 1. T检验示例
    control_values = np.random.normal(45, 10, 1000).tolist()
    treatment_values = np.random.normal(48, 10, 1000).tolist()
    
    result = analyzer.t_test(control_values, treatment_values)
    print("T检验结果:")
    print(f"  对照组均值: {result['control_mean']:.2f}")
    print(f"  实验组均值: {result['treatment_mean']:.2f}")
    print(f"  提升: {result['lift']:.2f}%")
    print(f"  P值: {result['p_value']:.4f}")
    print(f"  显著: {result['is_significant']}")
    print()
    
    # 2. 比例Z检验示例（CTR）
    result = analyzer.proportion_z_test(
        control_success=456,
        control_total=10000,
        treatment_success=523,
        treatment_total=10000
    )
    print("比例Z检验结果（CTR）:")
    print(f"  对照组CTR: {result['control_rate']:.4f}")
    print(f"  实验组CTR: {result['treatment_rate']:.4f}")
    print(f"  提升: {result['lift']:.2f}%")
    print(f"  P值: {result['p_value']:.4f}")
    print(f"  显著: {result['is_significant']}")
    print()
    
    # 3. 样本量计算
    n = analyzer.sample_size_calculator(
        baseline_rate=0.05,
        min_detectable_effect=0.1,  # 10%提升
        alpha=0.05,
        power=0.8
    )
    print(f"样本量计算: 每组需要 {n} 个样本")

