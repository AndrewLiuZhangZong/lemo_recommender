"""
模型服务化
负责模型加载、预测、热更新
"""
import torch
import torch.nn as nn
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from threading import Lock
from app.ml.model_registry import ModelRegistry, ModelVersion


class ModelServer:
    """
    模型服务器
    
    功能:
    - 模型加载和缓存
    - 批量预测
    - 模型热更新
    - 多模型管理
    """
    
    def __init__(
        self,
        registry: ModelRegistry,
        device: torch.device = None,
        max_batch_size: int = 1024
    ):
        self.registry = registry
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.max_batch_size = max_batch_size
        
        # 模型缓存
        self.models: Dict[str, nn.Module] = {}
        self.model_versions: Dict[str, str] = {}
        
        # 线程锁（用于模型更新）
        self.lock = Lock()
    
    def load_model(
        self,
        model_name: str,
        version: Optional[str] = None,
        model_class: type = None
    ) -> nn.Module:
        """
        加载模型
        
        Args:
            model_name: 模型名称
            version: 版本号（None表示最新）
            model_class: 模型类
            
        Returns:
            加载的模型
        """
        # 获取模型版本
        model_version = self.registry.get_model(model_name, version)
        if not model_version:
            raise ValueError(f"模型不存在: {model_name} v{version}")
        
        # 如果没有提供model_class，尝试从配置推断
        if model_class is None:
            model_type = model_version.config.get("model_name", "")
            if "wide_and_deep" in model_type.lower():
                from app.ml.models.wide_deep import WideAndDeep
                model_class = WideAndDeep
            elif "deepfm" in model_type.lower():
                from app.ml.models.deepfm import DeepFM
                model_class = DeepFM
            elif "two_tower" in model_type.lower():
                from app.ml.models.two_tower import TwoTowerModel
                model_class = TwoTowerModel
            else:
                raise ValueError(f"无法推断模型类型: {model_type}")
        
        # 创建模型实例
        model = model_class(model_version.config)
        
        # 加载权重
        checkpoint = torch.load(model_version.model_path, map_location=self.device)
        if "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)
        
        # 移动到设备并设置为评估模式
        model.to(self.device)
        model.eval()
        
        print(f"[ModelServer] 已加载模型: {model_name} v{model_version.version}")
        
        return model
    
    def register_model(
        self,
        model_name: str,
        version: Optional[str] = None,
        model_class: type = None
    ):
        """注册模型到服务器"""
        with self.lock:
            model = self.load_model(model_name, version, model_class)
            self.models[model_name] = model
            self.model_versions[model_name] = version or "latest"
        
        print(f"[ModelServer] 已注册模型: {model_name}")
    
    def predict(
        self,
        model_name: str,
        inputs: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """
        单次预测
        
        Args:
            model_name: 模型名称
            inputs: 输入特征
            
        Returns:
            预测结果
        """
        if model_name not in self.models:
            raise ValueError(f"模型未注册: {model_name}")
        
        model = self.models[model_name]
        
        # 移动输入到设备
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # 预测
        with torch.no_grad():
            outputs = model(inputs)
        
        return outputs
    
    def batch_predict(
        self,
        model_name: str,
        batch_inputs: List[Dict[str, torch.Tensor]]
    ) -> List[torch.Tensor]:
        """
        批量预测
        
        Args:
            model_name: 模型名称
            batch_inputs: 批量输入
            
        Returns:
            批量预测结果
        """
        results = []
        
        # 分批处理
        for i in range(0, len(batch_inputs), self.max_batch_size):
            batch = batch_inputs[i:i + self.max_batch_size]
            
            # 合并batch
            merged_inputs = {}
            for key in batch[0].keys():
                merged_inputs[key] = torch.stack([item[key] for item in batch])
            
            # 预测
            outputs = self.predict(model_name, merged_inputs)
            results.append(outputs)
        
        # 拼接结果
        return torch.cat(results, dim=0) if results else torch.tensor([])
    
    def update_model(
        self,
        model_name: str,
        version: Optional[str] = None,
        model_class: type = None
    ):
        """
        热更新模型
        
        Args:
            model_name: 模型名称
            version: 新版本号
            model_class: 模型类
        """
        print(f"[ModelServer] 开始更新模型: {model_name}")
        
        # 加载新模型
        new_model = self.load_model(model_name, version, model_class)
        
        # 原子更新
        with self.lock:
            old_version = self.model_versions.get(model_name)
            self.models[model_name] = new_model
            self.model_versions[model_name] = version or "latest"
        
        print(f"[ModelServer] 模型已更新: {model_name} ({old_version} → {version})")
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """列出所有已加载的模型"""
        models_info = {}
        for model_name, model in self.models.items():
            models_info[model_name] = {
                "version": self.model_versions[model_name],
                "device": str(self.device),
                "parameters": sum(p.numel() for p in model.parameters())
            }
        return models_info
    
    def unload_model(self, model_name: str):
        """卸载模型（释放内存）"""
        with self.lock:
            if model_name in self.models:
                del self.models[model_name]
                del self.model_versions[model_name]
                print(f"[ModelServer] 已卸载模型: {model_name}")
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息"""
        if model_name not in self.models:
            raise ValueError(f"模型未注册: {model_name}")
        
        model = self.models[model_name]
        version = self.model_versions[model_name]
        
        return {
            "model_name": model_name,
            "version": version,
            "device": str(self.device),
            "total_parameters": sum(p.numel() for p in model.parameters()),
            "trainable_parameters": sum(
                p.numel() for p in model.parameters() if p.requires_grad
            )
        }


# 使用示例
if __name__ == '__main__':
    from app.ml.models.deepfm import DeepFM
    
    # 创建注册中心和服务器
    registry = ModelRegistry("model_registry")
    server = ModelServer(registry)
    
    # 注册模型
    server.register_model("deepfm_vlog", model_class=DeepFM)
    
    # 查看已加载的模型
    print("\n已加载的模型:")
    for name, info in server.list_models().items():
        print(f"  - {name}: v{info['version']}, {info['parameters']:,} 参数")
    
    # 模拟预测
    inputs = {
        "user_id": torch.randint(0, 100000, (32,)),
        "item_id": torch.randint(0, 50000, (32,)),
        "category": torch.randint(0, 100, (32,)),
        "author": torch.randint(0, 10000, (32,)),
        "device": torch.randint(0, 10, (32,)),
        "city": torch.randint(0, 500, (32,)),
        "user_age": torch.randn(32, 1),
        "item_duration": torch.randn(32, 1),
        "item_hot_score": torch.randn(32, 1),
        "hour_of_day": torch.randn(32, 1)
    }
    
    # 预测
    outputs = server.predict("deepfm_vlog", inputs)
    print(f"\n预测结果: {outputs[:5]}")

