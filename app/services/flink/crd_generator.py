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
        "description": "测试/开发环境，极小数据量",
        "min_replicas": 1,
        "max_replicas": 2
    },
    "small": {
        "jobmanager": {"cpu": 0.5, "memory": "512m"},
        "taskmanager": {"cpu": 0.5, "memory": "512m"},
        "description": "小规模生产，QPS < 1000",
        "min_replicas": 1,
        "max_replicas": 3
    },
    "medium": {
        "jobmanager": {"cpu": 1.0, "memory": "1024m"},
        "taskmanager": {"cpu": 1.0, "memory": "1024m"},
        "description": "中等规模生产，QPS 1000-10000",
        "min_replicas": 2,
        "max_replicas": 5
    },
    "large": {
        "jobmanager": {"cpu": 2.0, "memory": "2048m"},
        "taskmanager": {"cpu": 2.0, "memory": "2048m"},
        "description": "大规模生产，QPS 10000-100000",
        "min_replicas": 2,
        "max_replicas": 10
    },
    "xlarge": {
        "jobmanager": {"cpu": 4.0, "memory": "4096m"},
        "taskmanager": {"cpu": 4.0, "memory": "4096m"},
        "description": "超大规模生产，QPS > 100000",
        "min_replicas": 3,
        "max_replicas": 20
    }
}

# 自动伸缩模式
AUTOSCALER_MODES = {
    "disabled": {
        "name": "禁用自动伸缩",
        "description": "固定资源，适合流量稳定的场景"
    },
    "reactive": {
        "name": "Flink Reactive Mode",
        "description": "根据可用资源自动调整并行度（Flink 1.13+）"
    },
    "hpa": {
        "name": "Kubernetes HPA",
        "description": "根据 CPU/内存使用率自动扩缩 TaskManager"
    },
    "hpa_reactive": {
        "name": "HPA + Reactive（推荐）",
        "description": "结合 HPA 和 Reactive Mode，业界最佳实践"
    },
    "scheduled": {
        "name": "定时伸缩",
        "description": "按时间表自动调整资源（工作日高峰扩容）"
    },
    "scheduled_hpa": {
        "name": "定时伸缩 + HPA",
        "description": "定时调整基准 + HPA 动态伸缩（美团/字节实践）"
    }
}

# 预定义的定时伸缩策略
SCHEDULED_SCALING_PRESETS = {
    "workday_peak": {
        "name": "工作日高峰",
        "description": "工作日 9:00-18:00 扩容，其他时间缩容",
        "schedules": [
            {
                "name": "morning-scale-up",
                "cron": "0 9 * * 1-5",  # 周一到周五 9:00
                "min_replicas": 3,
                "max_replicas": 10
            },
            {
                "name": "evening-scale-down",
                "cron": "0 18 * * 1-5",  # 周一到周五 18:00
                "min_replicas": 1,
                "max_replicas": 3
            },
            {
                "name": "weekend-scale-down",
                "cron": "0 0 * * 6",  # 周六 00:00
                "min_replicas": 1,
                "max_replicas": 2
            }
        ]
    },
    "24x7_peak": {
        "name": "全天候高峰",
        "description": "每天高峰时段（9:00-23:00）扩容",
        "schedules": [
            {
                "name": "daily-scale-up",
                "cron": "0 9 * * *",  # 每天 9:00
                "min_replicas": 2,
                "max_replicas": 8
            },
            {
                "name": "daily-scale-down",
                "cron": "0 23 * * *",  # 每天 23:00
                "min_replicas": 1,
                "max_replicas": 3
            }
        ]
    },
    "custom": {
        "name": "自定义",
        "description": "用户自定义定时伸缩规则",
        "schedules": []
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
    
    def _get_image_pull_policy(self) -> str:
        """
        获取镜像拉取策略
        
        业界最佳实践：
        - :latest 标签 -> Always（确保总是拉取最新版本）
        - 明确版本标签 -> IfNotPresent（减少网络流量，提高启动速度）
        
        可通过环境变量 FLINK_IMAGE_PULL_POLICY 覆盖（Always/IfNotPresent/Never）
        
        Returns:
            镜像拉取策略
        """
        import os
        
        # 优先使用环境变量配置
        env_policy = os.getenv("FLINK_IMAGE_PULL_POLICY", "").strip()
        if env_policy in ["Always", "IfNotPresent", "Never"]:
            return env_policy
        
        # 根据镜像标签自动判断
        if self.app_image.endswith(":latest") or ":dev" in self.app_image:
            # 开发环境：总是拉取最新版本
            return "Always"
        else:
            # 生产环境：使用缓存镜像（明确版本标签）
            return "IfNotPresent"
    
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
        
        # 获取自动伸缩配置
        autoscaler_config = self._get_autoscaler_config(template, request)
        
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
                "image": self.app_image,  # flink-app 镜像已包含 PyFlink 支持
                "imagePullPolicy": self._get_image_pull_policy(),
                "flinkVersion": "v2_0",  # Flink 2.0 最新版
                "flinkConfiguration": self._build_flink_configuration(
                    template, request, parallelism, autoscaler_config, jm_resources, tm_resources
                ),
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
                    "replicas": autoscaler_config.get("min_replicas", max(1, parallelism // 4))
                },
                "job": {
                    "jarURI": "local:///opt/flink/opt/flink-python_2.12-2.0.0.jar",  # Flink 2.0 Python JAR
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
        
        # 添加 HPA 配置（如果启用）
        if autoscaler_config.get("mode") in ["hpa", "hpa_reactive"]:
            crd["spec"]["mode"] = "native"  # HPA 需要 native 模式
            
        return crd
    
    def _build_flink_configuration(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest,
        parallelism: int,
        autoscaler_config: Dict[str, Any],
        jm_resources: Dict[str, Any],
        tm_resources: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        构建 Flink 配置
        
        Args:
            template: 作业模板
            request: 提交请求
            parallelism: 并行度
            autoscaler_config: 自动伸缩配置
            jm_resources: JobManager 资源配置
            tm_resources: TaskManager 资源配置
            
        Returns:
            Flink 配置字典
        """
        config = {
            "taskmanager.numberOfTaskSlots": str(parallelism),
            "python.client.executable": "python3",
            "python.executable": "python3",
            "state.backend": "hashmap",  # 使用内存状态后端（适合测试）
            "state.checkpoints.dir": "file:///tmp/flink-checkpoints",  # 使用临时目录
            "state.savepoints.dir": "file:///tmp/flink-savepoints",  # 使用临时目录
            "execution.checkpointing.interval": str(template.config.get("checkpoint_interval", 600000)),  # 10分钟
            "taskmanager.memory.managed.fraction": "0.1",
        }
        
        # 根据资源档位动态设置内存配置（只有在小内存环境才需要详细配置）
        # 如果内存 <= 512MB，使用紧凑配置；否则让 Flink 自动计算
        jm_memory = jm_resources["memory"]
        tm_memory = tm_resources["memory"]
        
        # 解析内存大小（单位：MB）
        jm_mem_mb = int(jm_memory.replace("m", "").replace("M", ""))
        tm_mem_mb = int(tm_memory.replace("m", "").replace("M", ""))
        
        # 只有在 <= 512MB 的小内存环境才需要详细配置
        if jm_mem_mb <= 512 or tm_mem_mb <= 512:
            # 512MB 极限配置
            config.update({
                "taskmanager.memory.process.size": "512m",
                "taskmanager.memory.flink.size": "256m",
                "taskmanager.memory.jvm-metaspace.size": "96m",
                "taskmanager.memory.jvm-overhead.min": "160m",
                "taskmanager.memory.jvm-overhead.max": "160m",
                "jobmanager.memory.process.size": "512m",
                "jobmanager.memory.flink.size": "256m",
                "jobmanager.memory.jvm-metaspace.size": "96m",
                "jobmanager.memory.jvm-overhead.min": "160m",
                "jobmanager.memory.jvm-overhead.max": "160m",
            })
        # 对于 >= 1GB 的配置，让 Flink 自动计算（更稳定）
        
        # 如果启用 Reactive Mode
        if autoscaler_config.get("mode") in ["reactive", "hpa_reactive"]:
            config["scheduler-mode"] = "reactive"
            config["jobmanager.adaptive-scheduler.min-parallelism-increase"] = "1"
            config["jobmanager.adaptive-scheduler.resource-stabilization-timeout"] = "10s"
        
        return config
    
    def _get_autoscaler_config(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest
    ) -> Dict[str, Any]:
        """
        获取自动伸缩配置
        
        Args:
            template: 作业模板
            request: 提交请求
            
        Returns:
            自动伸缩配置
        """
        # 获取自动伸缩模式
        autoscaler_mode = (
            request.job_config.get("autoscaler_mode") or
            template.config.get("autoscaler_mode") or
            "disabled"
        )
        
        # 获取资源档位（用于推荐的副本数）
        resource_profile = (
            request.job_config.get("resource_profile") or
            template.config.get("resource_profile") or
            "micro"
        )
        
        # 从资源档位获取推荐的副本数范围
        profile = RESOURCE_PROFILES.get(resource_profile, RESOURCE_PROFILES["micro"])
        min_replicas = profile.get("min_replicas", 1)
        max_replicas = profile.get("max_replicas", 2)
        
        # 允许用户自定义覆盖
        min_replicas = request.job_config.get("min_replicas") or template.config.get("min_replicas") or min_replicas
        max_replicas = request.job_config.get("max_replicas") or template.config.get("max_replicas") or max_replicas
        
        # CPU 目标使用率（HPA）
        target_cpu_utilization = (
            request.job_config.get("target_cpu_utilization") or
            template.config.get("target_cpu_utilization") or
            80  # 默认 80%
        )
        
        # 获取定时伸缩配置
        scaling_schedule = None
        if autoscaler_mode in ["scheduled", "scheduled_hpa"]:
            scaling_schedule = self._get_scaling_schedule(template, request)
        
        return {
            "mode": autoscaler_mode,
            "min_replicas": int(min_replicas),
            "max_replicas": int(max_replicas),
            "target_cpu_utilization": int(target_cpu_utilization),
            "scaling_schedule": scaling_schedule
        }
    
    def _get_scaling_schedule(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest
    ) -> Optional[Dict[str, Any]]:
        """
        获取定时伸缩配置
        
        Args:
            template: 作业模板
            request: 提交请求
            
        Returns:
            定时伸缩配置
        """
        # 获取定时伸缩预设
        scaling_preset = (
            request.job_config.get("scaling_preset") or
            template.config.get("scaling_preset")
        )
        
        if scaling_preset and scaling_preset in SCHEDULED_SCALING_PRESETS:
            # 使用预定义策略
            preset = SCHEDULED_SCALING_PRESETS[scaling_preset]
            return {
                "preset": scaling_preset,
                "name": preset["name"],
                "description": preset["description"],
                "schedules": preset["schedules"]
            }
        
        # 自定义定时伸缩规则
        custom_schedules = (
            request.job_config.get("scaling_schedules") or
            template.config.get("scaling_schedules")
        )
        
        if custom_schedules and isinstance(custom_schedules, list):
            return {
                "preset": "custom",
                "name": "自定义策略",
                "description": "用户自定义的定时伸缩规则",
                "schedules": custom_schedules
            }
        
        return None
    
    def _get_resource_config(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        获取资源配置（支持资源档位）
        
        优先级：
        1. 请求参数中的 resource_profile（资源档位）
        2. 模板配置中的 resource_profile（资源档位）
        3. 模板配置中的 jobmanager_cpu/memory 等自定义资源
        4. 默认使用 micro 档位
        
        Args:
            template: 作业模板
            request: 提交请求
            
        Returns:
            (jobmanager_resources, taskmanager_resources)
        """
        from loguru import logger
        
        # 1. 检查请求参数中是否指定了资源档位
        resource_profile = request.job_config.get("resource_profile")
        
        if resource_profile and resource_profile in RESOURCE_PROFILES:
            # 使用预定义的资源档位
            profile = RESOURCE_PROFILES[resource_profile]
            logger.info(f"✓ 使用请求参数中的资源档位: {resource_profile}")
            return profile["jobmanager"], profile["taskmanager"]
        
        # 2. 检查模板配置中是否指定了资源档位
        template_resource_profile = template.config.get("resource_profile")
        
        if template_resource_profile and template_resource_profile in RESOURCE_PROFILES:
            # 使用模板中的资源档位
            profile = RESOURCE_PROFILES[template_resource_profile]
            logger.info(f"✓ 使用模板配置中的资源档位: {template_resource_profile}, JM内存={profile['jobmanager']['memory']}, TM内存={profile['taskmanager']['memory']}")
            return profile["jobmanager"], profile["taskmanager"]
        
        # 3. 检查模板配置中是否有自定义资源配置
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
            logger.info(f"✓ 使用自定义资源配置: JM内存={jm_resources['memory']}, TM内存={tm_resources['memory']}")
            return jm_resources, tm_resources
        
        # 4. 默认使用 micro 档位（适合测试和小规模生产）
        profile = RESOURCE_PROFILES["micro"]
        logger.warning(f"⚠️ 未找到资源配置，使用默认 micro 档位: JM内存={profile['jobmanager']['memory']}, TM内存={profile['taskmanager']['memory']}")
        logger.warning(f"   模板config内容: {template.config}")
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
                        # Flink 2.0 对应的 Kafka Connector
                        resolved_jar_urls.append(
                            "https://repo1.maven.org/maven2/org/apache/flink/"
                            "flink-sql-connector-kafka/3.3.0-2.0/"
                            "flink-sql-connector-kafka-3.3.0-2.0.jar"
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
    
    def generate_hpa(
        self,
        deployment_name: str,
        autoscaler_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成 HorizontalPodAutoscaler（HPA）配置
        
        Args:
            deployment_name: FlinkDeployment 名称
            autoscaler_config: 自动伸缩配置
            
        Returns:
            HPA YAML (dict 格式)
        """
        hpa = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": f"{deployment_name}-hpa",
                "namespace": self.namespace,
                "labels": {
                    "app": "flink-job",
                    "deployment": deployment_name
                }
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "flink.apache.org/v1beta1",
                    "kind": "FlinkDeployment",
                    "name": deployment_name
                },
                "minReplicas": autoscaler_config.get("min_replicas", 1),
                "maxReplicas": autoscaler_config.get("max_replicas", 5),
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": autoscaler_config.get("target_cpu_utilization", 80)
                            }
                        }
                    }
                ],
                "behavior": {
                    "scaleDown": {
                        "stabilizationWindowSeconds": 300,  # 5 分钟稳定期
                        "policies": [
                            {
                                "type": "Percent",
                                "value": 50,
                                "periodSeconds": 60
                            }
                        ]
                    },
                    "scaleUp": {
                        "stabilizationWindowSeconds": 60,  # 1 分钟稳定期
                        "policies": [
                            {
                                "type": "Percent",
                                "value": 100,
                                "periodSeconds": 60
                            }
                        ]
                    }
                }
            }
        }
        
        return hpa
    
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

