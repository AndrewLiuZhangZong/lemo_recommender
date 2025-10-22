"""
模型训练相关的离线任务
"""
from typing import Dict, Any
from datetime import datetime, timedelta
import torch
from app.tasks.celery_app import celery_app
from app.core.database import get_database


@celery_app.task(name="app.tasks.model_tasks.train_model_daily", bind=True)
def train_model_daily(self, tenant_id: str = None, scenario_id: str = None):
    """
    每日模型训练任务
    
    流程:
    1. 从MongoDB提取训练数据（最近30天）
    2. 特征工程和数据预处理
    3. 模型训练
    4. 模型评估
    5. 注册到模型注册中心
    6. 如果效果更好，自动上线
    """
    print("=" * 60)
    print(f"  离线任务: 模型训练")
    print(f"  任务ID: {self.request.id}")
    print("=" * 60)
    
    db = get_database()
    
    # 获取需要训练的场景
    scenarios_query = {}
    if tenant_id:
        scenarios_query["tenant_id"] = tenant_id
    if scenario_id:
        scenarios_query["scenario_id"] = scenario_id
    
    scenarios = list(db.scenarios.find(scenarios_query))
    
    results = []
    
    for scenario in scenarios:
        tenant_id = scenario["tenant_id"]
        scenario_id = scenario["scenario_id"]
        
        print(f"\n训练场景: {tenant_id}/{scenario_id}")
        
        try:
            # 1. 准备训练数据
            train_data, val_data = _prepare_training_data(
                db, tenant_id, scenario_id
            )
            
            print(f"  训练集: {len(train_data)} 样本")
            print(f"  验证集: {len(val_data)} 样本")
            
            if len(train_data) < 1000:
                print("  训练数据不足，跳过")
                continue
            
            # 2. 训练模型
            model_info = _train_deepfm_model(
                train_data, val_data, tenant_id, scenario_id
            )
            
            print(f"  训练完成")
            print(f"  验证损失: {model_info['val_loss']:.4f}")
            print(f"  验证AUC: {model_info.get('val_auc', 0):.4f}")
            
            # 3. 注册模型
            # TODO: 集成ModelRegistry
            # registry.register_model(...)
            
            results.append({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "status": "success",
                "metrics": model_info
            })
            
        except Exception as e:
            print(f"  训练失败: {e}")
            results.append({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "status": "failed",
                "error": str(e)
            })
            continue
    
    print()
    print("=" * 60)
    print(f"  任务完成")
    print(f"  成功: {sum(1 for r in results if r['status'] == 'success')}")
    print(f"  失败: {sum(1 for r in results if r['status'] == 'failed')}")
    print("=" * 60)
    
    return {
        "task_id": self.request.id,
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }


def _prepare_training_data(db, tenant_id: str, scenario_id: str):
    """
    准备训练数据
    
    Returns:
        (train_data, val_data)
    """
    # 1. 获取最近30天的交互数据
    start_time = datetime.utcnow() - timedelta(days=30)
    
    interactions = list(db.interactions.find({
        "tenant_id": tenant_id,
        "scenario_id": scenario_id,
        "timestamp": {"$gte": start_time}
    }).limit(100000))
    
    # 2. 构造正负样本
    # 正样本: 有正向交互（view, like, favorite）
    # 负样本: 曝光但未点击（或随机采样）
    
    samples = []
    for inter in interactions:
        # 简化：将view/like/favorite视为正样本（label=1）
        # impression视为负样本（label=0）
        label = 1 if inter["action_type"] in ["view", "like", "favorite"] else 0
        
        sample = {
            "user_id": inter["user_id"],
            "item_id": inter["item_id"],
            "context": inter.get("context", {}),
            "label": label
        }
        samples.append(sample)
    
    # 3. 划分训练集和验证集（8:2）
    split_idx = int(len(samples) * 0.8)
    train_data = samples[:split_idx]
    val_data = samples[split_idx:]
    
    return train_data, val_data


def _train_deepfm_model(train_data, val_data, tenant_id: str, scenario_id: str):
    """
    训练DeepFM模型
    
    Returns:
        模型信息字典
    """
    # TODO: 实际训练逻辑
    # 1. 特征工程
    # 2. 创建DataLoader
    # 3. 初始化模型
    # 4. 训练循环
    # 5. 保存模型
    
    # 模拟训练结果
    model_info = {
        "model_name": "deepfm",
        "tenant_id": tenant_id,
        "scenario_id": scenario_id,
        "train_samples": len(train_data),
        "val_samples": len(val_data),
        "epochs": 10,
        "val_loss": 0.4523,
        "val_auc": 0.7834,
        "val_accuracy": 0.7245,
        "trained_at": datetime.utcnow().isoformat()
    }
    
    return model_info


@celery_app.task(name="app.tasks.model_tasks.evaluate_model")
def evaluate_model(model_name: str, version: str, test_data_path: str):
    """
    模型离线评估
    
    Args:
        model_name: 模型名称
        version: 模型版本
        test_data_path: 测试数据路径
    """
    print(f"[Task] 模型评估: {model_name} v{version}")
    
    # TODO: 实现模型评估
    # 1. 加载模型
    # 2. 加载测试数据
    # 3. 批量预测
    # 4. 计算指标（AUC, Accuracy, Precision, Recall）
    # 5. 返回评估报告
    
    return {
        "model_name": model_name,
        "version": version,
        "metrics": {
            "auc": 0.7834,
            "accuracy": 0.7245,
            "precision": 0.6892,
            "recall": 0.7123
        }
    }


@celery_app.task(name="app.tasks.model_tasks.export_model_for_serving")
def export_model_for_serving(model_name: str, version: str, export_format: str = "torchscript"):
    """
    导出模型用于线上服务
    
    Args:
        model_name: 模型名称
        version: 模型版本
        export_format: 导出格式（torchscript, onnx）
    """
    print(f"[Task] 导出模型: {model_name} v{version} -> {export_format}")
    
    # TODO: 实现模型导出
    # 1. 加载PyTorch模型
    # 2. 转换为指定格式
    # 3. 保存到指定路径
    
    return {
        "model_name": model_name,
        "version": version,
        "export_format": export_format,
        "export_path": f"models/{model_name}_{version}.{export_format}"
    }

