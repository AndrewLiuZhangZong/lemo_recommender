"""
实时计算配置加载器
用于 Flink 作业从 MongoDB 加载场景配置
"""
from typing import Dict, Tuple, List, Any
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)


class RealtimeConfigLoader:
    """
    实时计算配置加载器
    
    用于 Flink 作业从 MongoDB 动态加载场景配置
    支持多租户、多场景，按 (tenant_id, scenario_id) 索引配置
    """
    
    def __init__(self, mongodb_url: str, database: str):
        """
        初始化配置加载器
        
        Args:
            mongodb_url: MongoDB 连接字符串
            database: 数据库名称
        """
        self.mongodb_url = mongodb_url
        self.database = database
        self.configs: Dict[Tuple[str, str], dict] = {}  # (tenant_id, scenario_id) -> config
        
        logger.info(f"初始化 RealtimeConfigLoader: {database}")
    
    def load_configs(self) -> Dict[Tuple[str, str], dict]:
        """
        从 MongoDB 加载所有活跃场景的配置（同步方法，用于 Flink）
        
        Returns:
            配置字典：{(tenant_id, scenario_id): config}
        """
        try:
            client = MongoClient(self.mongodb_url)
            db = client[self.database]
            
            self.configs.clear()
            
            # 加载所有活跃场景
            scenarios = db.scenarios.find({'status': 'active'})
            
            for scenario in scenarios:
                key = (scenario['tenant_id'], scenario['scenario_id'])
                
                # 提取配置
                config = scenario.get('config', {})
                realtime_config = config.get('realtime_compute', {})
                
                self.configs[key] = {
                    'tenant_id': scenario['tenant_id'],
                    'scenario_id': scenario['scenario_id'],
                    'scenario_type': scenario.get('scenario_type', 'custom'),
                    'name': scenario.get('name', ''),
                    
                    # 实时计算配置
                    'hot_score': realtime_config.get('hot_score', {}),
                    'user_profile': realtime_config.get('user_profile', {}),
                    'metrics': realtime_config.get('metrics', {}),
                }
            
            client.close()
            
            logger.info(f"✅ 加载了 {len(self.configs)} 个场景的实时计算配置")
            return self.configs
            
        except Exception as e:
            logger.error(f"❌ 加载配置失败: {e}")
            return self.configs
    
    def get_config(self, tenant_id: str, scenario_id: str) -> dict:
        """
        获取指定场景的完整配置
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            
        Returns:
            场景配置字典
        """
        key = (tenant_id, scenario_id)
        return self.configs.get(key, {})
    
    def get_hot_score_config(self, tenant_id: str, scenario_id: str) -> dict:
        """
        获取热度计算配置
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            
        Returns:
            热度计算配置
        """
        config = self.get_config(tenant_id, scenario_id)
        return config.get('hot_score', {})
    
    def get_action_weights(self, tenant_id: str, scenario_id: str) -> dict:
        """
        获取行为权重
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            
        Returns:
            行为权重字典
        """
        hot_score_config = self.get_hot_score_config(tenant_id, scenario_id)
        
        # 默认权重
        default_weights = {
            'impression': 0.5,
            'view': 1.0,
            'click': 2.0,
            'like': 3.0,
            'favorite': 4.0,
            'comment': 5.0,
            'share': 6.0,
            'purchase': 10.0
        }
        
        return hot_score_config.get('action_weights', default_weights)
    
    def get_decay_lambda(self, tenant_id: str, scenario_id: str) -> float:
        """
        获取时间衰减系数
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            
        Returns:
            衰减系数（默认 0.1）
        """
        hot_score_config = self.get_hot_score_config(tenant_id, scenario_id)
        return hot_score_config.get('decay_lambda', 0.1)
    
    def get_window_config(self, tenant_id: str, scenario_id: str) -> Tuple[int, int]:
        """
        获取滑动窗口配置
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            
        Returns:
            (window_size_minutes, window_slide_minutes)
        """
        hot_score_config = self.get_hot_score_config(tenant_id, scenario_id)
        window_size = hot_score_config.get('window_size_minutes', 60)
        window_slide = hot_score_config.get('window_slide_minutes', 15)
        return window_size, window_slide
    
    def is_hot_score_enabled(self, tenant_id: str, scenario_id: str) -> bool:
        """
        检查热度计算是否启用
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            
        Returns:
            是否启用
        """
        hot_score_config = self.get_hot_score_config(tenant_id, scenario_id)
        return hot_score_config.get('enabled', True)
    
    def get_user_profile_config(self, tenant_id: str, scenario_id: str) -> dict:
        """
        获取用户画像更新配置
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            
        Returns:
            用户画像配置
        """
        config = self.get_config(tenant_id, scenario_id)
        return config.get('user_profile', {})
    
    def get_metrics_config(self, tenant_id: str, scenario_id: str) -> dict:
        """
        获取指标计算配置
        
        Args:
            tenant_id: 租户ID
            scenario_id: 场景ID
            
        Returns:
            指标计算配置
        """
        config = self.get_config(tenant_id, scenario_id)
        return config.get('metrics', {})
    
    def get_all_enabled_scenarios(self, job_type: str = 'hot_score') -> List[Tuple[str, str]]:
        """
        获取所有启用了指定作业类型的场景
        
        Args:
            job_type: 作业类型 ('hot_score', 'user_profile', 'metrics')
            
        Returns:
            启用的场景列表 [(tenant_id, scenario_id), ...]
        """
        enabled_scenarios = []
        
        for key, config in self.configs.items():
            job_config = config.get(job_type, {})
            if job_config.get('enabled', True):
                enabled_scenarios.append(key)
        
        return enabled_scenarios
    
    def print_summary(self):
        """打印配置摘要"""
        print("\n" + "=" * 70)
        print(f"📋 实时计算配置摘要（共 {len(self.configs)} 个场景）")
        print("=" * 70)
        
        if not self.configs:
            print("⚠️  未加载任何配置")
            return
        
        for key, config in self.configs.items():
            tenant_id, scenario_id = key
            print(f"\n🏷️  {tenant_id}/{scenario_id} ({config['scenario_type']})")
            print(f"   名称: {config['name']}")
            
            # 热度计算
            hot_score = config.get('hot_score', {})
            if hot_score.get('enabled', True):
                weights = hot_score.get('action_weights', {})
                print(f"   ✅ 热度计算: 启用")
                print(f"      - 衰减系数: {hot_score.get('decay_lambda', 0.1)}")
                print(f"      - 窗口大小: {hot_score.get('window_size_minutes', 60)}分钟")
                print(f"      - 购买权重: {weights.get('purchase', 10.0)}")
            else:
                print(f"   ❌ 热度计算: 禁用")
            
            # 用户画像
            user_profile = config.get('user_profile', {})
            if user_profile.get('enabled', True):
                print(f"   ✅ 用户画像: 启用（更新频率 {user_profile.get('update_frequency_minutes', 5)}分钟）")
            
            # 指标计算
            metrics = config.get('metrics', {})
            if metrics.get('enabled', True):
                print(f"   ✅ 指标计算: 启用")
        
        print("\n" + "=" * 70)

