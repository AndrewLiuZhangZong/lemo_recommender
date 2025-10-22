"""
作业管理服务
管理Flink作业、模型训练任务等的启动、停止、监控
"""
import subprocess
import asyncio
import signal
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class JobType(str, Enum):
    """作业类型"""
    FLINK = "flink"
    CELERY = "celery"
    MODEL_TRAINING = "model_training"
    DATA_SYNC = "data_sync"


class JobStatus(str, Enum):
    """作业状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"


class Job:
    """作业实例"""
    
    def __init__(
        self,
        job_id: str,
        name: str,
        job_type: JobType,
        command: List[str],
        description: str = ""
    ):
        self.job_id = job_id
        self.name = name
        self.job_type = job_type
        self.command = command
        self.description = description
        self.process: Optional[subprocess.Popen] = None
        self.status = JobStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.stop_time: Optional[datetime] = None
        self.restart_count = 0
        self.error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "job_type": self.job_type.value,
            "description": self.description,
            "status": self.status.value,
            "pid": self.process.pid if self.process else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stop_time": self.stop_time.isoformat() if self.stop_time else None,
            "restart_count": self.restart_count,
            "error_message": self.error_message,
            "is_running": self.is_running()
        }
    
    def is_running(self) -> bool:
        """检查是否运行中"""
        if self.process:
            return self.process.poll() is None
        return False


class JobManager:
    """
    作业管理器
    
    功能:
    1. 启动/停止作业
    2. 监控作业状态
    3. 自动重启（可选）
    4. 日志管理
    """
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # 预定义作业
        self._register_predefined_jobs()
    
    def _register_predefined_jobs(self):
        """注册预定义作业"""
        import sys
        from pathlib import Path
        
        project_root = Path(__file__).parent.parent.parent
        python_exe = sys.executable
        
        # Flink作业
        self.register_job(Job(
            job_id="flink_user_profile",
            name="用户画像实时更新",
            job_type=JobType.FLINK,
            command=[python_exe, str(project_root / "flink_jobs/user_profile_updater.py")],
            description="从Kafka消费用户行为，5分钟窗口聚合，更新用户画像"
        ))
        
        self.register_job(Job(
            job_id="flink_item_hot_score",
            name="物品热度实时计算",
            job_type=JobType.FLINK,
            command=[python_exe, str(project_root / "flink_jobs/item_hot_score_calculator.py")],
            description="1小时滑动窗口，计算物品热度到Redis"
        ))
        
        self.register_job(Job(
            job_id="flink_rec_metrics",
            name="推荐指标实时统计",
            job_type=JobType.FLINK,
            command=[python_exe, str(project_root / "flink_jobs/recommendation_metrics.py")],
            description="1分钟窗口聚合，推送指标到Prometheus"
        ))
        
        # Kafka消费者
        self.register_job(Job(
            job_id="kafka_item_consumer",
            name="物品数据Kafka消费者",
            job_type=JobType.CELERY,
            command=[python_exe, str(project_root / "scripts/run_item_consumer.py")],
            description="消费业务系统Kafka消息，接入物品数据"
        ))
        
        # Celery Worker
        self.register_job(Job(
            job_id="celery_worker",
            name="Celery异步任务Worker",
            job_type=JobType.CELERY,
            command=["celery", "-A", "app.tasks.celery_app", "worker", "-l", "info"],
            description="处理向量生成、相似度计算等异步任务"
        ))
        
        # Celery Beat
        self.register_job(Job(
            job_id="celery_beat",
            name="Celery定时任务调度器",
            job_type=JobType.CELERY,
            command=["celery", "-A", "app.tasks.celery_app", "beat", "-l", "info"],
            description="定时触发任务"
        ))
    
    def register_job(self, job: Job):
        """注册作业"""
        self.jobs[job.job_id] = job
    
    async def start_job(self, job_id: str) -> Dict[str, Any]:
        """启动作业"""
        if job_id not in self.jobs:
            return {"success": False, "message": f"作业不存在: {job_id}"}
        
        job = self.jobs[job_id]
        
        # 检查是否已运行
        if job.is_running():
            return {"success": False, "message": "作业已在运行中"}
        
        try:
            job.status = JobStatus.STARTING
            
            # 启动进程
            job.process = subprocess.Popen(
                job.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent.parent.parent)
            )
            
            job.status = JobStatus.RUNNING
            job.start_time = datetime.utcnow()
            job.error_message = None
            
            print(f"[JobManager] 启动作业: {job.name} (PID: {job.process.pid})")
            
            return {
                "success": True,
                "message": f"作业已启动: {job.name}",
                "job": job.to_dict()
            }
        
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            print(f"[JobManager] 启动失败: {job.name} - {e}")
            
            return {
                "success": False,
                "message": f"启动失败: {str(e)}",
                "job": job.to_dict()
            }
    
    async def stop_job(self, job_id: str, force: bool = False) -> Dict[str, Any]:
        """停止作业"""
        if job_id not in self.jobs:
            return {"success": False, "message": f"作业不存在: {job_id}"}
        
        job = self.jobs[job_id]
        
        if not job.is_running():
            return {"success": False, "message": "作业未运行"}
        
        try:
            job.status = JobStatus.STOPPING
            
            if force:
                # 强制杀死
                job.process.kill()
            else:
                # 优雅停止
                job.process.terminate()
            
            # 等待进程结束
            try:
                job.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                job.process.kill()
            
            job.status = JobStatus.STOPPED
            job.stop_time = datetime.utcnow()
            job.process = None
            
            print(f"[JobManager] 停止作业: {job.name}")
            
            return {
                "success": True,
                "message": f"作业已停止: {job.name}",
                "job": job.to_dict()
            }
        
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            print(f"[JobManager] 停止失败: {job.name} - {e}")
            
            return {
                "success": False,
                "message": f"停止失败: {str(e)}",
                "job": job.to_dict()
            }
    
    async def restart_job(self, job_id: str) -> Dict[str, Any]:
        """重启作业"""
        # 先停止
        stop_result = await self.stop_job(job_id)
        if not stop_result["success"] and "未运行" not in stop_result["message"]:
            return stop_result
        
        # 再启动
        await asyncio.sleep(1)
        start_result = await self.start_job(job_id)
        
        if start_result["success"]:
            self.jobs[job_id].restart_count += 1
        
        return start_result
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取作业状态"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        
        # 更新状态
        if job.process and job.process.poll() is not None:
            # 进程已退出
            if job.status == JobStatus.RUNNING:
                job.status = JobStatus.STOPPED
                job.stop_time = datetime.utcnow()
        
        return job.to_dict()
    
    def list_jobs(self, job_type: Optional[JobType] = None) -> List[Dict[str, Any]]:
        """列出所有作业"""
        jobs = []
        for job in self.jobs.values():
            if job_type is None or job.job_type == job_type:
                # 更新状态
                if job.process and job.process.poll() is not None:
                    if job.status == JobStatus.RUNNING:
                        job.status = JobStatus.STOPPED
                        job.stop_time = datetime.utcnow()
                
                jobs.append(job.to_dict())
        
        return jobs
    
    async def start_monitoring(self):
        """启动监控任务"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        print("[JobManager] 监控任务已启动")
    
    async def stop_monitoring(self):
        """停止监控任务"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        print("[JobManager] 监控任务已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        while self._monitoring:
            try:
                for job in self.jobs.values():
                    if job.process and job.process.poll() is not None:
                        # 进程已退出
                        if job.status == JobStatus.RUNNING:
                            job.status = JobStatus.STOPPED
                            job.stop_time = datetime.utcnow()
                            print(f"[JobManager] 作业已退出: {job.name}")
                
                await asyncio.sleep(5)  # 每5秒检查一次
            
            except Exception as e:
                print(f"[JobManager] 监控异常: {e}")
                await asyncio.sleep(5)
    
    async def stop_all_jobs(self):
        """停止所有作业"""
        print("[JobManager] 停止所有作业...")
        
        for job_id in list(self.jobs.keys()):
            if self.jobs[job_id].is_running():
                await self.stop_job(job_id)
        
        print("[JobManager] 所有作业已停止")


# 全局单例
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """获取作业管理器单例"""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager

