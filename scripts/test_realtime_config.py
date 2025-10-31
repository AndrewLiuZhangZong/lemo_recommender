#!/usr/bin/env python3
"""
测试实时计算配置加载器
验证从 MongoDB 加载场景配置的功能
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.realtime.config_loader import RealtimeConfigLoader
from app.core.config import settings


def test_config_loader():
    """测试配置加载器"""
    print("=" * 70)
    print("测试实时计算配置加载器")
    print("=" * 70)
    print()
    
    # 创建配置加载器
    print("📊 连接信息:")
    print(f"  - MongoDB URL: {settings.mongodb_url}")
    print(f"  - Database: {settings.mongodb_database}")
    print()
    
    loader = RealtimeConfigLoader(
        mongodb_url=settings.mongodb_url,
        mongodb_database=settings.mongodb_database
    )
    
    # 加载配置
    print("🔄 加载配置...")
    configs = loader.load_configs()
    
    if not configs:
        print("\n⚠️  未加载到任何配置")
        print("💡 请先在后台创建场景配置，或确保 MongoDB 中有数据")
        return
    
    # 打印配置摘要
    loader.print_summary()
    
    # 测试配置查询
    print("\n" + "=" * 70)
    print("🔍 测试配置查询")
    print("=" * 70)
    
    # 获取第一个场景进行测试
    first_key = list(configs.keys())[0]
    tenant_id, scenario_id = first_key
    
    print(f"\n测试场景: {tenant_id}/{scenario_id}")
    print()
    
    # 获取行为权重
    weights = loader.get_action_weights(tenant_id, scenario_id)
    print("📝 行为权重:")
    for action, weight in weights.items():
        print(f"  - {action}: {weight}")
    
    # 获取衰减系数
    decay = loader.get_decay_lambda(tenant_id, scenario_id)
    print(f"\n⏰ 时间衰减系数: {decay}")
    
    # 获取窗口配置
    window_size, window_slide = loader.get_window_config(tenant_id, scenario_id)
    print(f"\n🪟 滑动窗口配置:")
    print(f"  - 窗口大小: {window_size} 分钟")
    print(f"  - 滑动步长: {window_slide} 分钟")
    
    # 检查是否启用
    enabled = loader.is_hot_score_enabled(tenant_id, scenario_id)
    print(f"\n✅ 热度计算: {'启用' if enabled else '禁用'}")
    
    # 获取所有启用热度计算的场景
    enabled_scenarios = loader.get_all_enabled_scenarios('hot_score')
    print(f"\n📊 启用热度计算的场景数: {len(enabled_scenarios)}")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)


if __name__ == '__main__':
    try:
        test_config_loader()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

