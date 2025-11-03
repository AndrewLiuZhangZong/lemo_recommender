"""
Flink Deployment CRD 生成器

根据作业模板和提交请求生成 FlinkDeployment Custom Resource Definition
"""
from typing import Dict, Any, List, Optional
from app.models.flink_job_template import JobTemplate, FlinkJobSubmitRequest
import re


# 业界标准：预定义资源档位（参考阿里云 Flink、AWS Kinesis）
RESOURCE_PROFILES = {
    "micro": {
        "jobmanager": {"cpu": 0.2, "memory": "256m"},
        "taskmanager": {"cpu": 0.2, "memory": "256m"},
        "description": "测试/开发环境，极小数据量"
    },
    "small": {
        "jobmanager": {"cpu": 0.5, "memory": "512m"},
        "taskmanager": {"cpu": 0.5, "memory": "512m"},
        "description": "小规模生产，QPS < 1000"
    },
    "medium": {
        "jobmanager": {"cpu": 1.0, "memory": "1024m"},
        "taskmanager": {"cpu": 1.0, "memory": "1024m"},
        "description": "中等规模生产，QPS 1000-10000"
    },
    "large": {
        "jobmanager": {"cpu": 2.0, "memory": "2048m"},
        "taskmanager": {"cpu": 2.0, "memory": "2048m"},
        "description": "大规模生产，QPS 10000-100000"
    },
    "xlarge": {
        "jobmanager": {"cpu": 4.0, "memory": "4096m"},
        "taskmanager": {"cpu": 4.0, "memory": "4096m"},
        "description": "超大规模生产，QPS > 100000"
    }
}


class FlinkCRDGenerator:
    """Flink CRD 生成器"""
    
    def __init__(self, namespace: str = "lemo-dev", app_image: str = None):
        """
        初始化
        
        Args:
            namespace: K8s 命名空间
            app_image: Flink Application 镜像
        """
        self.namespace = namespace
        self.app_image = app_image or "registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest"
    
    def generate(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest
    ) -> Dict[str, Any]:
        """
        生成 FlinkDeployment CRD
        
        Args:
            template: 作业模板
            request: 提交请求
            
        Returns:
            FlinkDeployment YAML (dict 格式)
        """
        # 生成规范的资源名称
        resource_name = self._generate_resource_name(request.job_id)
        
        # 合并配置
        parallelism = int(request.job_config.get("parallelism", template.parallelism or 1))
        script_path = template.config.get("script_path")
        jar_files = template.config.get("jar_files", [])
        
        # 构建环境变量
        env_vars = self._build_env_vars(template, request, script_path, jar_files)
        
        # 获取资源配置（支持资源档位）
        jm_resources, tm_resources = self._get_resource_config(template, request)
        
        # 构建 FlinkDeployment CRD
        crd = {
            "apiVersion": "flink.apache.org/v1beta1",
            "kind": "FlinkDeployment",
            "metadata": {
                "name": resource_name,
                "namespace": self.namespace,
                "labels": {
                    "app": "flink-job",
                    "template-id": str(template.id),
                    "job-id": request.job_id,
                    "job-type": template.job_type.value,
                }
            },
            "spec": {
                "image": self.app_image,
                "imagePullPolicy": "IfNotPresent",
                "flinkVersion": "v1_19",
                "flinkConfiguration": {
                    "taskmanager.numberOfTaskSlots": str(parallelism),
                    "python.client.executable": "python3",
                    "python.executable": "python3",
                    "state.backend": "filesystem",
                    "state.checkpoints.dir": "file:///flink/checkpoints",
                    "state.savepoints.dir": "file:///flink/savepoints",
                    "execution.checkpointing.interval": str(template.config.get("checkpoint_interval", 300000)),
                },
                "serviceAccount": "lemo-service-recommender-sa",
                "podTemplate": {
                    "spec": {
                        "imagePullSecrets": [
                            {"name": "regcred"}
                        ]
                    }
                },
                "jobManager": {
                    "resource": {
                        "memory": jm_resources["memory"],
                        "cpu": jm_resources["cpu"]
                    }
                },
                "taskManager": {
                    "resource": {
                        "memory": tm_resources["memory"],
                        "cpu": tm_resources["cpu"]
                    },
                    "replicas": max(1, parallelism // 4)  # 每个 TM 4个 slot
                },
                "job": {
                    "jarURI": "local:///opt/flink/opt/flink-python-1.19.3.jar",
                    "entryClass": "org.apache.flink.client.python.PythonDriver",
                    "args": [
                        "-py",
                        "/opt/flink/usrlib/entrypoint.py"
                    ],
                    "parallelism": parallelism,
                    "upgradeMode": "stateless",
                    "state": "running",
                    "savepointTriggerNonce": 0
                }
            }
        }
        
        # 添加环境变量
        if env_vars:
            if "podTemplate" not in crd["spec"]:
                crd["spec"]["podTemplate"] = {"spec": {}}
            if "spec" not in crd["spec"]["podTemplate"]:
                crd["spec"]["podTemplate"]["spec"] = {}
            
            crd["spec"]["podTemplate"]["spec"]["containers"] = [
                {
                    "name": "flink-main-container",
                    "env": env_vars
                }
            ]
        
        return crd
    
    def _get_resource_config(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        获取资源配置（支持资源档位）
        
        优先级：
        1. 请求参数中的 resource_profile（资源档位）
        2. 模板配置中的 jobmanager_cpu/memory 等
        3. 默认使用 micro 档位
        
        Args:
            template: 作业模板
            request: 提交请求
            
        Returns:
            (jobmanager_resources, taskmanager_resources)
        """
        # 1. 检查请求参数中是否指定了资源档位
        resource_profile = request.job_config.get("resource_profile")
        
        if resource_profile and resource_profile in RESOURCE_PROFILES:
            # 使用预定义的资源档位
            profile = RESOURCE_PROFILES[resource_profile]
            return profile["jobmanager"], profile["taskmanager"]
        
        # 2. 检查模板配置中是否有自定义资源配置
        jm_cpu = template.config.get("jobmanager_cpu") or request.job_config.get("jobmanager_cpu")
        jm_memory = template.config.get("jobmanager_memory") or request.job_config.get("jobmanager_memory")
        tm_cpu = template.config.get("taskmanager_cpu") or request.job_config.get("taskmanager_cpu")
        tm_memory = template.config.get("taskmanager_memory") or request.job_config.get("taskmanager_memory")
        
        if jm_cpu or jm_memory or tm_cpu or tm_memory:
            # 使用自定义资源配置
            jm_resources = {
                "cpu": jm_cpu or RESOURCE_PROFILES["micro"]["jobmanager"]["cpu"],
                "memory": jm_memory or RESOURCE_PROFILES["micro"]["jobmanager"]["memory"]
            }
            tm_resources = {
                "cpu": tm_cpu or RESOURCE_PROFILES["micro"]["taskmanager"]["cpu"],
                "memory": tm_memory or RESOURCE_PROFILES["micro"]["taskmanager"]["memory"]
            }
            return jm_resources, tm_resources
        
        # 3. 默认使用 micro 档位（适合测试和小规模生产）
        profile = RESOURCE_PROFILES["micro"]
        return profile["jobmanager"], profile["taskmanager"]
    
    def _generate_resource_name(self, job_id: str) -> str:
        """
        生成符合 K8s RFC 1123 规范的资源名称
        
        Args:
            job_id: 作业 ID
            
        Returns:
            规范的资源名称
        """
        # 1. 转换为小写
        name = job_id.lower()
        
        # 2. 替换下划线为连字符
        name = name.replace('_', '-')
        
        # 3. 移除非法字符（只保留字母、数字、连字符、点）
        name = re.sub(r'[^a-z0-9\-.]', '', name)
        
        # 4. 确保以字母数字开头和结尾
        name = re.sub(r'^[^a-z0-9]+', '', name)
        name = re.sub(r'[^a-z0-9]+$', '', name)
        
        # 5. 限制长度为 63 字符
        if len(name) > 63:
            # 保留前30和后30字符，中间用短横线连接
            name = f"{name[:30]}-{name[-30:]}"
        
        # 6. 确保名称有效
        if not name or len(name) < 3:
            import time
            name = f"flink-job-{int(time.time())}"
        
        return name
    
    def _build_env_vars(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest,
        script_path: str,
        jar_files: List[str]
    ) -> List[Dict[str, str]]:
        """
        构建环境变量列表
        
        Args:
            template: 作业模板
            request: 提交请求
            script_path: 脚本路径
            jar_files: JAR 文件列表
            
        Returns:
            环境变量列表
        """
        env_vars = [
            {"name": "SCRIPT_URL", "value": script_path},
            {"name": "JOB_ID", "value": request.job_id},
            {"name": "JOB_NAME", "value": template.name},
        ]
        
        # 添加 JAR 依赖
        if jar_files:
            # 将本地路径转换为 Maven URL
            resolved_jar_urls = []
            for jar in jar_files:
                if jar.startswith("http://") or jar.startswith("https://"):
                    resolved_jar_urls.append(jar)
                else:
                    # 是本地路径，尝试映射到 Maven URL
                    if "kafka" in jar:
                        resolved_jar_urls.append(
                            "https://repo1.maven.org/maven2/org/apache/flink/"
                            "flink-sql-connector-kafka/3.0.2-1.18/"
                            "flink-sql-connector-kafka-3.0.2-1.18.jar"
                        )
            
            if resolved_jar_urls:
                env_vars.append({
                    "name": "JAR_URLS",
                    "value": ",".join(resolved_jar_urls)
                })
        
        # 添加 Kafka 配置
        if "kafka_bootstrap_servers" in request.job_config:
            env_vars.append({
                "name": "KAFKA_SERVERS",
                "value": request.job_config["kafka_bootstrap_servers"]
            })
        
        # 添加 Checkpoint 配置
        if "checkpoint_interval" in template.config:
            env_vars.append({
                "name": "CHECKPOINT_INTERVAL",
                "value": str(template.config["checkpoint_interval"])
            })
        
        # 添加自定义参数
        if "env" in request.job_config:
            for key, value in request.job_config["env"].items():
                env_vars.append({
                    "name": key.upper(),
                    "value": str(value)
                })
        
        return env_vars
    
    def to_yaml(self, crd: Dict[str, Any]) -> str:
        """
        将 CRD 转换为 YAML 字符串
        
        Args:
            crd: CRD 字典
            
        Returns:
            YAML 字符串
        """
        import yaml
        return yaml.dump(crd, default_flow_style=False, sort_keys=False)

