# Flink 作业状态同步机制

## 📖 概述

对于通过 Kubernetes Job 提交的 Flink Python 作业，我们实现了自动状态同步机制，用于：

1. **提取 Flink Job ID**：从 K8s Job 日志中提取真实的 Flink Job ID
2. **同步作业状态**：定期查询 Flink REST API 获取最新状态
3. **清理资源**：自动清理已完成的 K8s Job

---

## 🔄 工作流程

### 1. 作业提交阶段

```
用户提交作业
    ↓
创建 MongoDB 记录 (status: CREATED, flink_job_id: null)
    ↓
创建 K8s Job
    ↓
返回 K8s Job 名称作为临时 job_id
```

### 2. K8s Job 执行阶段

```
K8s Job Pod 启动
    ↓
执行: /opt/flink/bin/flink run -py script.py
    ↓
Flink CLI 输出日志:
  "Job has been submitted with JobID abc123def456..."
    ↓
作业在 Flink 集群中开始运行
    ↓
K8s Job 完成并退出 (状态: Succeeded)
```

### 3. 状态同步阶段 (Celery 定时任务)

```
每3分钟执行一次
    ↓
查询所有非最终状态的作业 (CREATED, RUNNING, SUSPENDED)
    ↓
对于每个作业:
  ├─ 如果没有 flink_job_id:
  │   ├─ 查询 K8s Job 状态
  │   ├─ 如果 Job 成功: 读取 Pod 日志
  │   ├─ 正则提取 Flink Job ID
  │   └─ 更新 MongoDB (flink_job_id, status: RUNNING)
  │
  └─ 如果有 flink_job_id:
      ├─ 调用 Flink REST API: GET /jobs/{flink_job_id}
      ├─ 映射 Flink 状态到系统状态
      ├─ 计算运行时长 (如果已完成)
      └─ 更新 MongoDB
```

---

## 🎯 状态映射

| Flink 状态 | 系统状态 | 说明 |
|------------|---------|------|
| CREATED | CREATED | 作业已创建 |
| RUNNING | RUNNING | 作业运行中 |
| FINISHED | FINISHED | 作业已完成 |
| FAILED | FAILED | 作业失败 |
| CANCELED | CANCELLED | 作业已取消 |
| CANCELLING | RUNNING | 取消中（视为运行） |
| RESTARTING | RUNNING | 重启中（视为运行） |
| SUSPENDED | SUSPENDED | 作业已暂停 |

---

## ⏰ 定时任务配置

### 1. 状态同步任务

- **任务名称**: `sync_flink_job_status`
- **执行频率**: 每 3 分钟
- **功能**: 同步所有非最终状态作业

```python
# Celery Beat 配置
"sync-flink-job-status-3min": {
    "task": "sync_flink_job_status",
    "schedule": crontab(minute="*/3"),
}
```

### 2. K8s Job 清理任务

- **任务名称**: `cleanup_completed_k8s_jobs`
- **执行频率**: 每天凌晨 2:00
- **功能**: 清理超过 24 小时的已完成 K8s Job

```python
# Celery Beat 配置
"cleanup-k8s-jobs-daily": {
    "task": "cleanup_completed_k8s_jobs",
    "schedule": crontab(minute=0, hour=2),
}
```

---

## 🔍 查看作业状态

### 方法 1: 前端页面

1. 打开 **Flink 作业管理** 页面
2. 切换到 **作业实例** 标签页
3. 查看作业状态列
4. 点击 **详情** 按钮查看完整信息

### 方法 2: MongoDB 查询

```javascript
// 连接 MongoDB
use lemo_recommender

// 查询作业
db.flink_jobs.find({
  "job_id": "your_job_id"
}).pretty()

// 查看字段
{
  "job_id": "template_id_timestamp",
  "flink_job_id": "abc123def456...",  // Flink 真实 Job ID
  "status": "RUNNING",
  "submitted_at": "2025-11-01T12:00:00",
  "start_time": "2025-11-01T12:00:30",
  "end_time": null,
  "duration": null
}
```

### 方法 3: Flink Web UI

1. 访问: `http://111.228.39.41:8081`
2. 查看 **Running Jobs** 或 **Completed Jobs**
3. 使用 `flink_job_id` 搜索

### 方法 4: Kubernetes 命令

```bash
# 查看 K8s Job
kubectl get jobs -n lemo-dev -l app=flink-python-job

# 查看 K8s Job Pod
kubectl get pods -n lemo-dev -l app=flink-python-job

# 查看 Pod 日志（提取 Flink Job ID）
kubectl logs -n lemo-dev <pod-name> | grep "Job has been submitted"

# 输出示例:
# Job has been submitted with JobID abc123def456789...
```

### 方法 5: Flink REST API

```bash
# 获取所有作业
curl http://111.228.39.41:8081/jobs

# 获取指定作业详情
curl http://111.228.39.41:8081/jobs/{flink_job_id}

# 响应示例:
{
  "jid": "abc123def456...",
  "name": "Python Job",
  "state": "RUNNING",
  "start-time": 1730444400000,
  "end-time": -1,
  "duration": 60000
}
```

---

## 🛠️ 故障排查

### 问题 1: 作业一直是 CREATED 状态

**可能原因**:
- K8s Job 创建失败
- K8s Job Pod 无法启动
- 镜像拉取失败

**排查步骤**:
```bash
# 1. 检查 K8s Job
kubectl get jobs -n lemo-dev -l app=flink-python-job

# 2. 检查 Pod 状态
kubectl get pods -n lemo-dev -l app=flink-python-job

# 3. 查看 Pod 详情
kubectl describe pod -n lemo-dev <pod-name>

# 4. 查看 Pod 日志
kubectl logs -n lemo-dev <pod-name>
```

### 问题 2: 无法提取 Flink Job ID

**可能原因**:
- Flink 命令执行失败
- 日志格式不匹配
- 网络问题导致无法连接 Flink

**排查步骤**:
```bash
# 1. 查看完整日志
kubectl logs -n lemo-dev <pod-name>

# 2. 检查是否有错误信息
kubectl logs -n lemo-dev <pod-name> | grep -i error

# 3. 检查 Flink 连接
curl http://111.228.39.41:8081/overview
```

### 问题 3: 状态同步不及时

**可能原因**:
- Celery Beat 未启动
- 定时任务配置错误
- Flink REST API 不可达

**排查步骤**:
```bash
# 1. 检查 Beat 服务
kubectl logs -n lemo-dev -l app=lemo-service-recommender-beat

# 2. 手动触发同步任务
# 在 Worker 容器中执行:
python3 -c "
from app.tasks.flink_tasks import sync_flink_job_status
sync_flink_job_status()
"

# 3. 检查 Flink REST API
curl http://111.228.39.41:8081/jobs
```

---

## 📊 监控指标

### 1. 作业状态分布

```javascript
// MongoDB 查询
db.flink_jobs.aggregate([
  {
    $group: {
      _id: "$status",
      count: { $sum: 1 }
    }
  }
])
```

### 2. 平均运行时长

```javascript
// MongoDB 查询
db.flink_jobs.aggregate([
  {
    $match: {
      status: "FINISHED",
      duration: { $ne: null }
    }
  },
  {
    $group: {
      _id: null,
      avg_duration: { $avg: "$duration" },
      min_duration: { $min: "$duration" },
      max_duration: { $max: "$duration" }
    }
  }
])
```

### 3. 失败率统计

```javascript
// MongoDB 查询
db.flink_jobs.aggregate([
  {
    $group: {
      _id: null,
      total: { $sum: 1 },
      failed: {
        $sum: {
          $cond: [{ $eq: ["$status", "FAILED"] }, 1, 0]
        }
      }
    }
  },
  {
    $project: {
      total: 1,
      failed: 1,
      failure_rate: {
        $multiply: [
          { $divide: ["$failed", "$total"] },
          100
        ]
      }
    }
  }
])
```

---

## 🚀 性能优化建议

### 1. 调整同步频率

根据业务需求调整定时任务频率：

```python
# 高频场景（实时性要求高）
"schedule": crontab(minute="*/1"),  # 每1分钟

# 中频场景（默认）
"schedule": crontab(minute="*/3"),  # 每3分钟

# 低频场景（降低开销）
"schedule": crontab(minute="*/10"),  # 每10分钟
```

### 2. 索引优化

为 MongoDB 添加索引：

```javascript
// 创建索引
db.flink_jobs.createIndex({ "status": 1 })
db.flink_jobs.createIndex({ "job_id": 1 })
db.flink_jobs.createIndex({ "flink_job_id": 1 })
db.flink_jobs.createIndex({ "submitted_at": -1 })
```

### 3. 批量查询

对于大量作业，使用批量查询减少 API 调用：

```python
# 未来优化: 使用 Flink /jobs/overview API 批量获取状态
response = await self.client.get("/jobs/overview")
all_jobs = response.json()["jobs"]
```

---

## 📚 参考文档

- [Flink REST API 文档](https://nightlies.apache.org/flink/flink-docs-release-1.19/docs/ops/rest_api/)
- [Kubernetes Job 文档](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [Celery Beat 文档](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)


