# Flink 配置化改造方案

## 📌 问题分析

### 当前问题
Flink 作业参数全部硬编码，无法根据后台配置动态运行：

```python
# ❌ 当前：硬编码
self.action_weights = {
    'impression': 0.5,
    'view': 1.0,
    'click': 2.0,
    # ...
}
self.decay_lambda = 0.1
```

### 目标
- ✅ 根据 **Scenario 配置** 动态计算
- ✅ 支持 **多租户、多场景**
- ✅ 配置变更后**自动生效**（或重启）
- ✅ 符合业界最佳实践

---

## 🏗️ 业界最佳实践

### 方案对比

| 方案 | 代表 | 适用场景 | 优势 | 劣势 |
|------|------|---------|------|------|
| **Flink SQL Platform** | StreamPark、Zeppelin | UI 配置作业 | 可视化、易用 | 需要独立平台 |
| **元数据驱动** | 字节、美团 | 配置中心驱动 | 灵活、支持热更新 | 需要配置管理 |
| **作业模板化** | 阿里云实时计算 | 参数化作业 | 标准化、易维护 | 模板设计复杂 |
| **混合方案** | 推荐 ⭐ | **元数据 + 模板** | 兼顾灵活性和标准化 | - |

### 推荐方案：**元数据驱动 + 作业模板化**

**核心思路：**
1. **配置在 MongoDB**：Scenario 配置定义实时计算参数
2. **作业读取配置**：Flink 作业启动时从 MongoDB 加载
3. **多场景并行**：一个 Flink 作业处理多个场景，根据 `(tenant_id, scenario_id)` 动态应用配置
4. **配置热更新**：定期刷新配置（或通过 Broadcast State）

---

## 🎯 改造方案

### 第1步：扩展 Scenario 配置模型

在 `app/models/scenario.py` 中添加 **实时计算配置**：

```python
class RealtimeComputeConfig(BaseModel):
    """实时计算配置（用于 Flink 作业）"""
    
    # 1. 热度计算配置
    hot_score: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": True,  # 是否启用热度计算
            "action_weights": {
                "impression": 0.5,
                "view": 1.0,
                "click": 2.0,
                "like": 3.0,
                "favorite": 4.0,
                "comment": 5.0,
                "share": 6.0,
                "purchase": 10.0
            },
            "decay_lambda": 0.1,  # 时间衰减系数
            "window_size_minutes": 60,  # 滑动窗口大小（分钟）
            "window_slide_minutes": 15,  # 滑动步长（分钟）
        },
        description="物品热度计算配置"
    )
    
    # 2. 用户画像更新配置
    user_profile: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": True,
            "update_frequency_minutes": 5,  # 更新频率
            "interest_decay_days": 30,  # 兴趣衰减周期
            "behavior_weights": {
                "view": 1.0,
                "like": 3.0,
                "favorite": 5.0,
                "purchase": 10.0
            }
        },
        description="用户画像更新配置"
    )
    
    # 3. 推荐指标计算配置
    metrics: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": True,
            "window_size_minutes": 30,
            "metrics_to_calculate": ["ctr", "cvr", "watch_time"]
        },
        description="推荐指标计算配置"
    )

class ScenarioConfig(BaseModel):
    """场景配置详情"""
    # ... 现有配置 ...
    
    # 新增：实时计算配置
    realtime_compute: RealtimeComputeConfig = Field(
        default_factory=RealtimeComputeConfig,
        description="实时计算配置（Flink 作业使用）"
    )
```

### 第2步：创建配置加载器

创建 `app/services/realtime/config_loader.py`：

```python
"""实时计算配置加载器"""
import asyncio
from typing import Dict, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import MongoClient
from app.core.config import settings


class RealtimeConfigLoader:
    """实时计算配置加载器（用于 Flink 作业）"""
    
    def __init__(self, mongodb_url: str, database: str):
        self.mongodb_url = mongodb_url
        self.database = database
        self.configs: Dict[Tuple[str, str], dict] = {}  # (tenant_id, scenario_id) -> config
    
    def load_configs(self):
        """从 MongoDB 加载所有活跃场景的配置（同步方法，用于 Flink）"""
        client = MongoClient(self.mongodb_url)
        db = client[self.database]
        
        self.configs.clear()
        
        # 加载所有活跃场景
        scenarios = db.scenarios.find({'status': 'active'})
        
        for scenario in scenarios:
            key = (scenario['tenant_id'], scenario['scenario_id'])
            
            # 提取实时计算配置
            realtime_config = scenario.get('config', {}).get('realtime_compute', {})
            
            self.configs[key] = {
                'tenant_id': scenario['tenant_id'],
                'scenario_id': scenario['scenario_id'],
                'scenario_type': scenario.get('scenario_type', 'custom'),
                'hot_score': realtime_config.get('hot_score', {}),
                'user_profile': realtime_config.get('user_profile', {}),
                'metrics': realtime_config.get('metrics', {}),
            }
        
        client.close()
        
        print(f"✅ 加载了 {len(self.configs)} 个场景的实时计算配置")
        return self.configs
    
    def get_config(self, tenant_id: str, scenario_id: str, config_type: str = 'hot_score') -> dict:
        """获取指定场景的配置"""
        key = (tenant_id, scenario_id)
        scenario_config = self.configs.get(key, {})
        return scenario_config.get(config_type, {})
    
    def get_action_weights(self, tenant_id: str, scenario_id: str) -> dict:
        """获取行为权重"""
        hot_score_config = self.get_config(tenant_id, scenario_id, 'hot_score')
        return hot_score_config.get('action_weights', {
            'impression': 0.5, 'view': 1.0, 'click': 2.0,
            'like': 3.0, 'favorite': 4.0, 'comment': 5.0,
            'share': 6.0, 'purchase': 10.0
        })
    
    def get_decay_lambda(self, tenant_id: str, scenario_id: str) -> float:
        """获取时间衰减系数"""
        hot_score_config = self.get_config(tenant_id, scenario_id, 'hot_score')
        return hot_score_config.get('decay_lambda', 0.1)
```

### 第3步：改造 Flink 作业

修改 `flink_jobs/item_hot_score_calculator.py`：

```python
class ItemHotScoreCalculator:
    """物品热度实时计算（配置驱动版）"""
    
    def __init__(self, kafka_servers, redis_url, mongodb_url, mongodb_database):
        self.kafka_servers = kafka_servers
        self.redis_url = redis_url
        
        # 配置加载器
        self.config_loader = RealtimeConfigLoader(mongodb_url, mongodb_database)
        self.config_loader.load_configs()  # 初始加载
        
        # 启动配置刷新线程（每5分钟刷新一次）
        self._start_config_refresh_thread()
    
    def _start_config_refresh_thread(self):
        """启动配置刷新线程"""
        import threading
        import time
        
        def refresh():
            while True:
                time.sleep(300)  # 5分钟
                try:
                    self.config_loader.load_configs()
                    print("🔄 配置已刷新")
                except Exception as e:
                    print(f"⚠️  配置刷新失败: {e}")
        
        thread = threading.Thread(target=refresh, daemon=True)
        thread.start()
        print("✅ 配置刷新线程已启动")
    
    def run(self):
        """运行 Flink 作业（配置驱动）"""
        # ... Flink 环境初始化 ...
        
        # 处理函数：根据 (tenant_id, scenario_id) 应用不同配置
        class DynamicHotScoreCalculator(ProcessWindowFunction):
            def __init__(self, config_loader):
                self.config_loader = config_loader
            
            def process(self, key, context, elements):
                tenant_id, scenario_id, item_id = key
                
                # 🔥 动态获取配置
                action_weights = self.config_loader.get_action_weights(tenant_id, scenario_id)
                decay_lambda = self.config_loader.get_decay_lambda(tenant_id, scenario_id)
                
                # 计算热度（使用动态配置）
                # ... 计算逻辑 ...
                
                yield hot_score_data
        
        # 使用动态配置计算器
        hot_scores = (
            behaviors
            .key_by(lambda x: (x['tenant_id'], x['scenario_id'], x['item_id']))
            .window(SlidingProcessingTimeWindows.of(
                Time.minutes(60),
                Time.minutes(15)
            ))
            .process(DynamicHotScoreCalculator(self.config_loader))
        )
        
        # ... 后续处理 ...
```

---

## 🚀 部署流程

### 方式1：单一 Flink 作业（推荐）

**一个 Flink 作业处理所有场景**，根据 `(tenant_id, scenario_id)` 动态应用配置。

```bash
# 启动 Flink 作业
python scripts/run_flink_jobs.py \
  --job item_hot_score \
  --mongodb-url mongodb://... \
  --kafka-servers 111.228.39.41:9092 \
  --redis-url redis://...
```

**优势：**
- ✅ 资源利用高
- ✅ 管理简单
- ✅ 配置变更后自动生效（定期刷新）

### 方式2：按场景启动（高级）

为每个重要场景启动独立 Flink 作业。

```bash
# 为特定场景启动
python scripts/run_flink_jobs.py \
  --job item_hot_score \
  --tenant-id tenant_001 \
  --scenario-id vlog_main_feed \
  --mongodb-url mongodb://...
```

**优势：**
- ✅ 资源隔离
- ✅ 故障隔离
- ❌ 管理复杂

---

## 🔄 配置更新流程

### 1. 管理员在后台修改 Scenario 配置
```
HTTP POST /api/v1/scenarios/{scenario_id}
{
  "config": {
    "realtime_compute": {
      "hot_score": {
        "action_weights": {
          "purchase": 15.0  // 提高购买权重
        }
      }
    }
  }
}
```

### 2. 配置写入 MongoDB
```
scenarios.update_one(
  {"tenant_id": "...", "scenario_id": "..."},
  {"$set": {"config.realtime_compute": ...}}
)
```

### 3. Flink 作业自动刷新配置
```
[每5分钟]
  → 从 MongoDB 重新加载配置
  → 更新内存中的配置字典
  → 后续计算使用新配置 ✅
```

---

## 📊 对比表

| 维度 | 改造前 | 改造后 |
|------|--------|--------|
| **配置方式** | ❌ 代码硬编码 | ✅ MongoDB 配置 |
| **多场景支持** | ❌ 不支持 | ✅ 支持无限场景 |
| **配置变更** | ❌ 需要改代码、重新部署 | ✅ 后台修改、自动刷新 |
| **租户隔离** | ❌ 不支持 | ✅ 支持多租户 |
| **业务灵活性** | ❌ 低 | ✅ 高 |
| **运维成本** | ❌ 高 | ✅ 低 |

---

## ✅ 总结

### 符合业界最佳实践
- ✅ **元数据驱动**：配置存储在 MongoDB
- ✅ **作业模板化**：通用 Flink 作业，支持多场景
- ✅ **动态参数**：根据场景 ID 动态应用配置
- ✅ **配置热更新**：定期刷新配置

### 下一步
1. 扩展 Scenario 模型（添加 `realtime_compute` 字段）
2. 创建 `RealtimeConfigLoader`
3. 改造 3 个 Flink 作业
4. 测试配置驱动的计算
5. 部署到生产环境

---

## 📚 参考资料

- [Apache Flink 最佳实践](https://nightlies.apache.org/flink/flink-docs-release-1.17/)
- [字节跳动实时计算平台](https://www.infoq.cn/article/bytedance-flink-practice)
- [美团巨鲸任务调度平台](https://tech.meituan.com/2021/11/04/flink-in-meituan.html)
- [阿里云实时计算 Flink 版](https://help.aliyun.com/zh/flink/)

