"""
模型版本管理和注册中心
"""
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib


class ModelVersion:
    """模型版本信息"""
    
    def __init__(
        self,
        model_name: str,
        version: str,
        model_path: Path,
        config: Dict[str, Any],
        metrics: Dict[str, float],
        created_at: str,
        description: str = ""
    ):
        self.model_name = model_name
        self.version = version
        self.model_path = model_path
        self.config = config
        self.metrics = metrics
        self.created_at = created_at
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "version": self.version,
            "model_path": str(self.model_path),
            "config": self.config,
            "metrics": self.metrics,
            "created_at": self.created_at,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelVersion":
        return cls(
            model_name=data["model_name"],
            version=data["version"],
            model_path=Path(data["model_path"]),
            config=data["config"],
            metrics=data["metrics"],
            created_at=data["created_at"],
            description=data.get("description", "")
        )


class ModelRegistry:
    """
    模型注册中心
    
    功能:
    - 模型版本管理
    - 模型注册/加载
    - 版本比较和回滚
    - 模型元数据存储
    """
    
    def __init__(self, registry_dir: str = "model_registry"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        
        # 模型存储目录
        self.models_dir = self.registry_dir / "models"
        self.models_dir.mkdir(exist_ok=True)
        
        # 元数据文件
        self.metadata_file = self.registry_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """加载元数据"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {"models": {}}
    
    def _save_metadata(self):
        """保存元数据"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def register_model(
        self,
        model_name: str,
        model_path: str,
        config: Dict[str, Any],
        metrics: Dict[str, float],
        description: str = "",
        version: Optional[str] = None
    ) -> ModelVersion:
        """
        注册模型
        
        Args:
            model_name: 模型名称
            model_path: 模型文件路径
            config: 模型配置
            metrics: 评估指标
            description: 描述
            version: 版本号（可选，默认自动生成）
            
        Returns:
            ModelVersion对象
        """
        # 生成版本号
        if version is None:
            version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # 创建模型目录
        model_dir = self.models_dir / model_name / version
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制模型文件
        model_file = model_dir / "model.pt"
        shutil.copy(model_path, model_file)
        
        # 保存配置
        config_file = model_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 保存指标
        metrics_file = model_dir / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        # 创建版本对象
        model_version = ModelVersion(
            model_name=model_name,
            version=version,
            model_path=model_file,
            config=config,
            metrics=metrics,
            created_at=datetime.utcnow().isoformat(),
            description=description
        )
        
        # 更新元数据
        if model_name not in self.metadata["models"]:
            self.metadata["models"][model_name] = {
                "versions": [],
                "latest_version": None
            }
        
        self.metadata["models"][model_name]["versions"].append(
            model_version.to_dict()
        )
        self.metadata["models"][model_name]["latest_version"] = version
        
        self._save_metadata()
        
        print(f"[ModelRegistry] 已注册模型: {model_name} v{version}")
        print(f"  - 路径: {model_file}")
        print(f"  - 指标: {metrics}")
        
        return model_version
    
    def get_model(
        self,
        model_name: str,
        version: Optional[str] = None
    ) -> Optional[ModelVersion]:
        """
        获取模型版本
        
        Args:
            model_name: 模型名称
            version: 版本号（None表示最新版本）
            
        Returns:
            ModelVersion对象或None
        """
        if model_name not in self.metadata["models"]:
            return None
        
        model_meta = self.metadata["models"][model_name]
        
        # 使用最新版本
        if version is None:
            version = model_meta["latest_version"]
        
        # 查找版本
        for ver_data in model_meta["versions"]:
            if ver_data["version"] == version:
                return ModelVersion.from_dict(ver_data)
        
        return None
    
    def list_versions(self, model_name: str) -> List[ModelVersion]:
        """列出模型所有版本"""
        if model_name not in self.metadata["models"]:
            return []
        
        versions = []
        for ver_data in self.metadata["models"][model_name]["versions"]:
            versions.append(ModelVersion.from_dict(ver_data))
        
        # 按时间排序
        versions.sort(key=lambda v: v.created_at, reverse=True)
        
        return versions
    
    def list_models(self) -> List[str]:
        """列出所有模型"""
        return list(self.metadata["models"].keys())
    
    def set_latest_version(self, model_name: str, version: str):
        """设置最新版本（用于版本回滚）"""
        if model_name not in self.metadata["models"]:
            raise ValueError(f"模型不存在: {model_name}")
        
        # 验证版本是否存在
        versions = [v["version"] for v in self.metadata["models"][model_name]["versions"]]
        if version not in versions:
            raise ValueError(f"版本不存在: {version}")
        
        self.metadata["models"][model_name]["latest_version"] = version
        self._save_metadata()
        
        print(f"[ModelRegistry] 已切换到版本: {model_name} v{version}")
    
    def delete_version(self, model_name: str, version: str):
        """删除模型版本"""
        if model_name not in self.metadata["models"]:
            raise ValueError(f"模型不存在: {model_name}")
        
        model_meta = self.metadata["models"][model_name]
        
        # 查找并删除版本
        versions = model_meta["versions"]
        for i, ver_data in enumerate(versions):
            if ver_data["version"] == version:
                # 删除文件
                model_dir = self.models_dir / model_name / version
                if model_dir.exists():
                    shutil.rmtree(model_dir)
                
                # 删除元数据
                del versions[i]
                break
        
        # 如果删除的是最新版本，更新latest_version
        if model_meta["latest_version"] == version:
            if versions:
                model_meta["latest_version"] = versions[-1]["version"]
            else:
                model_meta["latest_version"] = None
        
        self._save_metadata()
        
        print(f"[ModelRegistry] 已删除版本: {model_name} v{version}")
    
    def compare_versions(
        self,
        model_name: str,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """比较两个版本"""
        ver1 = self.get_model(model_name, version1)
        ver2 = self.get_model(model_name, version2)
        
        if not ver1 or not ver2:
            return {}
        
        comparison = {
            "version1": version1,
            "version2": version2,
            "metrics_diff": {},
            "config_diff": {}
        }
        
        # 比较指标
        for metric_name in set(list(ver1.metrics.keys()) + list(ver2.metrics.keys())):
            val1 = ver1.metrics.get(metric_name, 0)
            val2 = ver2.metrics.get(metric_name, 0)
            comparison["metrics_diff"][metric_name] = {
                "version1": val1,
                "version2": val2,
                "diff": val2 - val1,
                "improvement": ((val2 - val1) / val1 * 100) if val1 != 0 else 0
            }
        
        return comparison
    
    def get_best_model(
        self,
        model_name: str,
        metric_name: str = "val_loss",
        higher_is_better: bool = False
    ) -> Optional[ModelVersion]:
        """
        获取最佳模型（根据指标）
        
        Args:
            model_name: 模型名称
            metric_name: 指标名称
            higher_is_better: 是否越高越好
            
        Returns:
            最佳模型版本
        """
        versions = self.list_versions(model_name)
        
        if not versions:
            return None
        
        # 过滤有该指标的版本
        valid_versions = [v for v in versions if metric_name in v.metrics]
        
        if not valid_versions:
            return None
        
        # 排序
        valid_versions.sort(
            key=lambda v: v.metrics[metric_name],
            reverse=higher_is_better
        )
        
        return valid_versions[0]


# 使用示例
if __name__ == '__main__':
    # 创建注册中心
    registry = ModelRegistry("model_registry")
    
    # 注册模型
    model_version = registry.register_model(
        model_name="deepfm_vlog",
        model_path="models/model_best.pt",
        config={
            "embedding_dim": 16,
            "dnn_hidden_dims": [256, 128, 64]
        },
        metrics={
            "val_loss": 0.4523,
            "auc": 0.7834,
            "accuracy": 0.7245
        },
        description="DeepFM模型用于vlog场景CTR预估"
    )
    
    # 列出所有模型
    print("\n所有模型:")
    for model_name in registry.list_models():
        print(f"  - {model_name}")
    
    # 列出版本
    print("\n所有版本:")
    for version in registry.list_versions("deepfm_vlog"):
        print(f"  - v{version.version}: AUC={version.metrics.get('auc', 0):.4f}")
    
    # 获取最佳模型
    best_model = registry.get_best_model("deepfm_vlog", "auc", higher_is_better=True)
    if best_model:
        print(f"\n最佳模型: v{best_model.version}")

