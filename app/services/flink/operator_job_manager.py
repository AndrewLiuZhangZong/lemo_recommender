"""
Flink Kubernetes Operator 作业管理器

通过 Kubernetes API 管理 FlinkDeployment CRD
"""
from typing import Optional
from kubernetes import client as k8s_client, config as k8s_config
from kubernetes.client.rest import ApiException
from loguru import logger

from app.models.flink_job_template import JobTemplate, FlinkJobSubmitRequest
from app.services.flink.crd_generator import FlinkCRDGenerator


class OperatorJobManager:
    """Flink Operator 作业管理器"""
    
    def __init__(self, namespace: str = "lemo-dev", app_image: str = None):
        """
        初始化
        
        Args:
            namespace: K8s 命名空间
            app_image: Flink Application 镜像
        """
        self.namespace = namespace
        self.app_image = app_image
        self.crd_generator = FlinkCRDGenerator(namespace, app_image)
        
        # 加载 K8s 配置
        try:
            k8s_config.load_incluster_config()
            logger.info("✓ 加载 K8s in-cluster 配置")
        except Exception:
            try:
                k8s_config.load_kube_config()
                logger.info("✓ 加载 K8s kubeconfig 配置")
            except Exception as e:
                raise RuntimeError(f"无法加载 Kubernetes 配置: {e}")
        
        # 创建 CustomObjects API 客户端
        self.custom_api = k8s_client.CustomObjectsApi()
    
    async def submit_job(
        self,
        template: JobTemplate,
        request: FlinkJobSubmitRequest
    ) -> str:
        """
        提交 Flink 作业
        
        Args:
            template: 作业模板
            request: 提交请求
            
        Returns:
            FlinkDeployment 名称
        """
        # 生成 CRD
        crd = self.crd_generator.generate(template, request)
        resource_name = crd["metadata"]["name"]
        
        # 获取自动伸缩配置
        autoscaler_config = self.crd_generator._get_autoscaler_config(template, request)
        autoscaler_mode = autoscaler_config.get("mode", "disabled")
        
        logger.info(f"准备提交 FlinkDeployment: {resource_name}")
        logger.info(f"作业类型: {template.job_type.value}, 并行度: {crd['spec']['job']['parallelism']}")
        logger.info(f"自动伸缩: {autoscaler_mode}, 副本范围: {autoscaler_config.get('min_replicas')}-{autoscaler_config.get('max_replicas')}")
        
        try:
            # 创建 FlinkDeployment CRD
            self.custom_api.create_namespaced_custom_object(
                group="flink.apache.org",
                version="v1beta1",
                namespace=self.namespace,
                plural="flinkdeployments",
                body=crd
            )
            
            logger.info(f"✓ FlinkDeployment 创建成功: {resource_name}")
            
            # 如果启用了 HPA，创建 HPA 资源
            if autoscaler_mode in ["hpa", "hpa_reactive", "scheduled_hpa"]:
                await self._create_hpa(resource_name, autoscaler_config)
            
            # 如果启用了定时伸缩，创建 CronJob
            if autoscaler_mode in ["scheduled", "scheduled_hpa"]:
                await self._create_scaling_cronjobs(resource_name, autoscaler_config)
            
            return resource_name
            
        except ApiException as e:
            logger.error(f"✗ FlinkDeployment 创建失败: {e}")
            raise RuntimeError(f"创建 FlinkDeployment 失败: {e.reason}")
    
    async def get_job_status(self, job_name: str) -> Optional[dict]:
        """
        获取作业状态
        
        Args:
            job_name: 作业名称（FlinkDeployment 名称）
            
        Returns:
            作业状态信息
        """
        try:
            deployment = self.custom_api.get_namespaced_custom_object(
                group="flink.apache.org",
                version="v1beta1",
                namespace=self.namespace,
                plural="flinkdeployments",
                name=job_name
            )
            
            status = deployment.get("status", {})
            job_status = status.get("jobStatus", {})
            
            return {
                "state": job_status.get("state", "UNKNOWN"),
                "job_id": job_status.get("jobId"),
                "start_time": job_status.get("startTime"),
                "update_time": job_status.get("updateTime"),
                "savepoint_info": job_status.get("savepointInfo"),
                "task_manager": {
                    "replicas": status.get("taskManager", {}).get("replicas", 0),
                    "ready_replicas": status.get("taskManager", {}).get("readyReplicas", 0),
                },
                "job_manager_deployment_status": status.get("jobManagerDeploymentStatus"),
                "reconciliation_status": status.get("reconciliationStatus", {}),
                "error": status.get("error")
            }
            
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"FlinkDeployment 不存在: {job_name}")
                return None
            logger.error(f"获取 FlinkDeployment 状态失败: {e}")
            raise
    
    async def stop_job(self, job_name: str, with_savepoint: bool = True) -> bool:
        """
        停止作业
        
        Args:
            job_name: 作业名称
            with_savepoint: 是否创建 Savepoint
            
        Returns:
            是否成功
        """
        try:
            # 获取当前 FlinkDeployment
            deployment = self.custom_api.get_namespaced_custom_object(
                group="flink.apache.org",
                version="v1beta1",
                namespace=self.namespace,
                plural="flinkdeployments",
                name=job_name
            )
            
            # 更新 job.state 为 suspended
            deployment["spec"]["job"]["state"] = "suspended"
            
            if with_savepoint:
                # 触发 savepoint
                current_nonce = deployment["spec"]["job"].get("savepointTriggerNonce", 0)
                deployment["spec"]["job"]["savepointTriggerNonce"] = current_nonce + 1
            
            # 更新 CRD
            self.custom_api.replace_namespaced_custom_object(
                group="flink.apache.org",
                version="v1beta1",
                namespace=self.namespace,
                plural="flinkdeployments",
                name=job_name,
                body=deployment
            )
            
            logger.info(f"✓ FlinkDeployment 已设置为 suspended: {job_name}")
            return True
            
        except ApiException as e:
            logger.error(f"✗ 停止 FlinkDeployment 失败: {e}")
            return False
    
    async def delete_job(self, job_name: str) -> bool:
        """
        删除作业
        
        Args:
            job_name: 作业名称
            
        Returns:
            是否成功
        """
        try:
            # 删除定时伸缩 CronJob（如果存在）
            await self._delete_scaling_cronjobs(job_name)
            
            # 删除 HPA（如果存在）
            await self._delete_hpa(job_name)
            
            # 删除 FlinkDeployment
            self.custom_api.delete_namespaced_custom_object(
                group="flink.apache.org",
                version="v1beta1",
                namespace=self.namespace,
                plural="flinkdeployments",
                name=job_name
            )
            
            logger.info(f"✓ FlinkDeployment 已删除: {job_name}")
            return True
            
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"FlinkDeployment 不存在，无需删除: {job_name}")
                return True
            logger.error(f"✗ 删除 FlinkDeployment 失败: {e}")
            return False
    
    async def list_jobs(self, label_selector: str = None) -> list:
        """
        列出作业
        
        Args:
            label_selector: 标签选择器，如 "app=flink-job"
            
        Returns:
            作业列表
        """
        try:
            result = self.custom_api.list_namespaced_custom_object(
                group="flink.apache.org",
                version="v1beta1",
                namespace=self.namespace,
                plural="flinkdeployments",
                label_selector=label_selector
            )
            
            return result.get("items", [])
            
        except ApiException as e:
            logger.error(f"✗ 列出 FlinkDeployment 失败: {e}")
            return []
    
    async def _create_hpa(self, deployment_name: str, autoscaler_config: dict):
        """
        创建 HorizontalPodAutoscaler
        
        Args:
            deployment_name: FlinkDeployment 名称
            autoscaler_config: 自动伸缩配置
        """
        try:
            hpa = self.crd_generator.generate_hpa(deployment_name, autoscaler_config)
            
            # 使用 autoscaling/v2 API
            from kubernetes import client as k8s_client
            autoscaling_api = k8s_client.AutoscalingV2Api()
            
            autoscaling_api.create_namespaced_horizontal_pod_autoscaler(
                namespace=self.namespace,
                body=hpa
            )
            
            logger.info(f"✓ HPA 创建成功: {hpa['metadata']['name']}")
            logger.info(f"  副本范围: {autoscaler_config['min_replicas']}-{autoscaler_config['max_replicas']}")
            logger.info(f"  目标 CPU: {autoscaler_config['target_cpu_utilization']}%")
            
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.warning(f"HPA 已存在，跳过创建: {deployment_name}-hpa")
            else:
                logger.error(f"✗ HPA 创建失败: {e}")
                # 不抛出异常，HPA 创建失败不影响作业提交
    
    async def _delete_hpa(self, deployment_name: str):
        """
        删除 HorizontalPodAutoscaler
        
        Args:
            deployment_name: FlinkDeployment 名称
        """
        try:
            from kubernetes import client as k8s_client
            autoscaling_api = k8s_client.AutoscalingV2Api()
            
            hpa_name = f"{deployment_name}-hpa"
            autoscaling_api.delete_namespaced_horizontal_pod_autoscaler(
                name=hpa_name,
                namespace=self.namespace
            )
            
            logger.info(f"✓ HPA 删除成功: {hpa_name}")
            
        except ApiException as e:
            if e.status == 404:  # Not found
                logger.debug(f"HPA 不存在，跳过删除: {deployment_name}-hpa")
            else:
                logger.warning(f"HPA 删除失败: {e}")
    
    async def _create_scaling_cronjobs(self, deployment_name: str, autoscaler_config: dict):
        """
        创建定时伸缩 CronJob
        
        Args:
            deployment_name: FlinkDeployment 名称
            autoscaler_config: 自动伸缩配置
        """
        scaling_schedule = autoscaler_config.get("scaling_schedule")
        if not scaling_schedule or not scaling_schedule.get("schedules"):
            logger.warning(f"定时伸缩配置为空，跳过创建 CronJob: {deployment_name}")
            return
        
        try:
            from kubernetes import client as k8s_client
            batch_api = k8s_client.BatchV1Api()
            
            for schedule in scaling_schedule["schedules"]:
                cronjob_name = f"{deployment_name}-scale-{schedule['name']}"
                cron_expression = schedule["cron"]
                min_replicas = schedule["min_replicas"]
                max_replicas = schedule["max_replicas"]
                
                # 创建 CronJob 来调整 HPA 或 FlinkDeployment 的副本数
                cronjob = {
                    "apiVersion": "batch/v1",
                    "kind": "CronJob",
                    "metadata": {
                        "name": cronjob_name,
                        "namespace": self.namespace,
                        "labels": {
                            "app": "flink-job-scaler",
                            "deployment": deployment_name,
                            "schedule-name": schedule["name"]
                        }
                    },
                    "spec": {
                        "schedule": cron_expression,
                        "concurrencyPolicy": "Forbid",  # 禁止并发执行
                        "successfulJobsHistoryLimit": 3,
                        "failedJobsHistoryLimit": 3,
                        "jobTemplate": {
                            "spec": {
                                "template": {
                                    "metadata": {
                                        "labels": {
                                            "app": "flink-job-scaler"
                                        }
                                    },
                                    "spec": {
                                        "serviceAccountName": "lemo-service-recommender-sa",
                                        "restartPolicy": "OnFailure",
                                        "containers": [
                                            {
                                                "name": "kubectl",
                                                "image": "bitnami/kubectl:latest",
                                                "command": [
                                                    "sh",
                                                    "-c",
                                                    f"""
                                                    echo "定时伸缩: {schedule['name']}"
                                                    echo "调整副本范围: {min_replicas}-{max_replicas}"
                                                    
                                                    # 如果有 HPA，更新 HPA 的副本范围
                                                    if kubectl get hpa {deployment_name}-hpa -n {self.namespace} 2>/dev/null; then
                                                        kubectl patch hpa {deployment_name}-hpa -n {self.namespace} \
                                                            --type merge -p '{{"spec":{{"minReplicas":{min_replicas},"maxReplicas":{max_replicas}}}}}'
                                                        echo "✓ HPA 副本范围已更新"
                                                    else
                                                        # 否则直接更新 FlinkDeployment 的副本数
                                                        kubectl patch flinkdeployment {deployment_name} -n {self.namespace} \
                                                            --type merge -p '{{"spec":{{"taskManager":{{"replicas":{min_replicas}}}}}}}'
                                                        echo "✓ FlinkDeployment 副本数已更新"
                                                    fi
                                                    """
                                                ]
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
                
                batch_api.create_namespaced_cron_job(
                    namespace=self.namespace,
                    body=cronjob
                )
                
                logger.info(f"✓ 定时伸缩 CronJob 创建成功: {cronjob_name}")
                logger.info(f"  Cron: {cron_expression}, 副本: {min_replicas}-{max_replicas}")
            
            logger.info(f"✓ 创建了 {len(scaling_schedule['schedules'])} 个定时伸缩任务")
            
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.warning(f"定时伸缩 CronJob 已存在，跳过创建")
            else:
                logger.error(f"✗ 定时伸缩 CronJob 创建失败: {e}")
                # 不抛出异常，CronJob 创建失败不影响作业提交
    
    async def _delete_scaling_cronjobs(self, deployment_name: str):
        """
        删除定时伸缩 CronJob
        
        Args:
            deployment_name: FlinkDeployment 名称
        """
        try:
            from kubernetes import client as k8s_client
            batch_api = k8s_client.BatchV1Api()
            
            # 查找所有相关的 CronJob
            cronjobs = batch_api.list_namespaced_cron_job(
                namespace=self.namespace,
                label_selector=f"deployment={deployment_name}"
            )
            
            for cronjob in cronjobs.items:
                batch_api.delete_namespaced_cron_job(
                    name=cronjob.metadata.name,
                    namespace=self.namespace
                )
                logger.info(f"✓ 定时伸缩 CronJob 删除成功: {cronjob.metadata.name}")
            
        except ApiException as e:
            if e.status == 404:  # Not found
                logger.debug(f"定时伸缩 CronJob 不存在，跳过删除")
            else:
                logger.warning(f"定时伸缩 CronJob 删除失败: {e}")

