# Flink Kubernetes Operator 架构与部署完整指南

## 📖 目录

1. [架构概述](#架构概述)
2. [核心组件](#核心组件)
3. [部署架构](#部署架构)
4. [部署步骤](#部署步骤)
5. [作业提交流程](#作业提交流程)
6. [运维管理](#运维管理)
7. [故障排查](#故障排查)

---

## 🏗️ 架构概述

### 设计理念

我们采用 **Flink Kubernetes Operator + Application Mode** 架构，这是业界标准的云原生 Flink 部署方案，被阿里云、字节跳动、美团等公司广泛使用。

### 核心优势

| 特性 | 传统 Session 模式 | Operator Application 模式 ✅ |
|------|------------------|----------------------------|
| **资源隔离** | ❌ 共享集群 | ✅ 每个作业独立集群 |
| **故障隔离** | ❌ 一个作业失败影响其他作业 | ✅ 作业间完全隔离 |
| **资源利用** | ❌ 需预留资源 | ✅ 按需分配，自动扩缩容 |
| **运维管理** | ❌ 手动管理生命周期 | ✅ Operator 自动管理 |
| **多租户支持** | ❌ 资源争抢 | ✅ 完全隔离 |
| **部署复杂度** | 🟡 中等 | 🟢 简单（声明式） |

---

## 🧩 核心组件

### 组件关系图

```
┌─────────────────────────────────────────────────────────────────┐
│                         服务器2 (K8s 集群)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Namespace: flink-operator-system              │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │  Flink Kubernetes Operator (Pod)                     │ │  │
│  │  │  - 监听 FlinkDeployment CRD                          │ │  │
│  │  │  - 自动创建/管理 JobManager & TaskManager            │ │  │
│  │  │  - 处理故障恢复、扩缩容                               │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  Namespace: lemo-dev                       │  │
│  │  ┌────────────────────────────────────────────────────┐   │  │
│  │  │  推荐服务 (HTTP/gRPC/Worker/Beat/Consumer)          │   │  │
│  │  │  - 创建 FlinkDeployment CRD                         │   │  │
│  │  │  - 查询作业状态                                      │   │  │
│  │  └────────────────────────────────────────────────────┘   │  │
│  │                                                             │  │
│  │  ┌────────────────────────────────────────────────────┐   │  │
│  │  │  FlinkDeployment: job-example-py (CRD)             │   │  │
│  │  │    ├─ JobManager Pod                               │   │  │
│  │  │    │   - 调度和协调                                 │   │  │
│  │  │    │   - REST API (8081)                           │   │  │
│  │  │    └─ TaskManager Pod(s)                           │   │  │
│  │  │        - 执行任务                                   │   │  │
│  │  │        - 运行 Python 脚本                           │   │  │
│  │  └────────────────────────────────────────────────────┘   │  │
│  │                                                             │  │
│  │  ┌────────────────────────────────────────────────────┐   │  │
│  │  │  FlinkDeployment: job-example-jar (CRD)            │   │  │
│  │  │    ├─ JobManager Pod                               │   │  │
│  │  │    └─ TaskManager Pod(s)                           │   │  │
│  │  └────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 组件说明

#### 1. **Flink Kubernetes Operator**
- **位置**: `flink-operator-system` namespace
- **职责**:
  - 监听 `FlinkDeployment` 自定义资源（CRD）
  - 自动创建和管理 Flink 集群（JobManager + TaskManager）
  - 处理作业的生命周期（启动、停止、重启、扩缩容）
  - 管理 Checkpoint、Savepoint
  - 故障自动恢复

#### 2. **FlinkDeployment CRD**
- **定义**: Kubernetes 自定义资源，声明式描述 Flink 作业
- **内容**:
  - 镜像配置
  - 资源配置（CPU、内存）
  - 作业参数（脚本 URL、并行度等）
  - Flink 配置（checkpoint、状态后端等）

#### 3. **JobManager Pod**
- **每个作业一个**，负责：
  - 作业调度和协调
  - Checkpoint 协调
  - 故障恢复
  - REST API 服务（端口 8081）

#### 4. **TaskManager Pod(s)**
- **可多个**，负责：
  - 执行具体的任务
  - 运行用户代码（Python 脚本、JAR 等）
  - 管理状态数据

#### 5. **推荐服务**
- **位置**: `lemo-dev` namespace
- **职责**:
  - 接收用户提交的作业请求
  - 生成 `FlinkDeployment` YAML
  - 通过 K8s API 创建 CRD
  - 查询作业状态（通过 K8s API）

---

## 🌐 部署架构

### 服务器规划

| 服务器 | IP | 用途 | 组件 |
|--------|-----|------|------|
| **服务器1** | `111.228.39.41` | ~~Flink Session 集群~~（已停用） | - |
| **服务器2** | `117.72.196.41` | K8s 集群 (K3s) | Operator、推荐服务、Flink 作业 |

### 网络架构

```
用户/前端
   │
   ├─> HTTP API ──> 推荐服务 (K8s Service)
   │                   │
   │                   ├─> K8s API Server
   │                   │   └─> 创建 FlinkDeployment CRD
   │                   │
   │                   └─> 查询作业状态
   │
   └─> 外部依赖:
       ├─> MongoDB: 111.228.39.41:27017
       ├─> Redis: 111.228.39.41:6379
       ├─> Kafka: 111.228.39.41:9092
       └─> (Flink 作业通过 K8s Service 访问这些依赖)
```

---

## 🚀 部署步骤

### 前提条件

1. ✅ K8s 集群已部署 (K3s)
2. ✅ kubectl 已配置
3. ✅ Helm 已安装（可选，推荐）
4. ✅ Docker 本地环境可构建镜像
5. ✅ ACR 镜像仓库可访问

### 步骤1: 准备 kubeconfig

```bash
# 在服务器2上
cp /etc/rancher/k3s/k3s.yaml /root/k3s-jd-config.yaml

# 修改 server 地址为外网 IP
vi /root/k3s-jd-config.yaml
# 将 server: https://127.0.0.1:6443
# 改为 server: https://117.72.196.41:6443

# 或者在本地 Mac 上
# 将 k3s-jd-config.yaml 放到项目的 k8s-deploy/ 目录
```

### 步骤2: 安装 Flink Kubernetes Operator

**在本地 Mac 或服务器2上执行：**

```bash
# 方式A: 在项目目录中执行
cd /path/to/lemo_recommender
bash scripts/install_flink_operator.sh

# 方式B: 远程执行（在服务器2上）
ssh root@117.72.196.41
cd /root/lemo_recommender
bash scripts/install_flink_operator.sh
```

**脚本会自动：**
1. 检测 kubeconfig 路径
2. 安装 cert-manager（Operator 依赖）
3. 安装 Flink Kubernetes Operator
4. 验证安装状态

**预期输出：**
```
========================================
✓ Flink Kubernetes Operator 安装成功！
========================================

验证命令：
  kubectl get pods -n flink-operator-system
  kubectl get crd | grep flink
```

### 步骤3: 验证 Operator 安装

```bash
export KUBECONFIG=/root/k3s-jd-config.yaml

# 查看 Operator Pod
kubectl get pods -n flink-operator-system
# 输出：
# NAME                                         READY   STATUS    RESTARTS   AGE
# flink-kubernetes-operator-xxx                1/1     Running   0          5m

# 查看 CRD
kubectl get crd | grep flink
# 输出：
# flinkdeployments.flink.apache.org     2025-11-03T05:33:54Z
# flinksessionjobs.flink.apache.org     2025-11-03T05:33:55Z
```

### 步骤4: 构建并推送 Flink Application 镜像

```bash
cd /path/to/lemo_recommender

# 构建镜像
docker build -f Dockerfile.flink-app \
  -t registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest .

# 推送到 ACR
docker login registry.cn-beijing.aliyuncs.com
docker push registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest
```

### 步骤5: 部署推荐服务

**使用现有的部署脚本：**

```bash
cd /path/to/lemo_recommender

# 部署 HTTP 和 gRPC 服务
bash k8s-deploy/deploy-http-grpc-service.sh

# 部署 Worker 服务
bash k8s-deploy/deploy-worker-service.sh

# 部署 Beat 服务
bash k8s-deploy/deploy-beat-service.sh

# 部署 Consumer 服务
bash k8s-deploy/deploy-consumer-service.sh
```

### 步骤6: 验证推荐服务部署

```bash
export KUBECONFIG=/root/k3s-jd-config.yaml

# 查看所有 Pod
kubectl get pods -n lemo-dev

# 查看 HTTP 服务日志，确认 Operator 模式已启用
kubectl logs -n lemo-dev deployment/lemo-service-recommender-http | grep -i operator
# 应该看到：
# ✓ Flink Operator 模式已启用（业界标准架构）
#   - Namespace: lemo-dev
#   - App Image: registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest
```

---

## 📋 作业提交流程

### 整体流程图

```
用户在前端创建作业模板
   │
   ├─> 1. 前端提交作业请求
   │      POST /api/v1/flink/jobs/submit
   │      {
   │        "template_id": "xxx",
   │        "job_config": { "parallelism": 2 }
   │      }
   │
   ├─> 2. Python 后端处理
   │      ├─ job_manager.submit_job()
   │      ├─ operator_manager.submit_job()
   │      └─ crd_generator.generate_yaml()
   │
   ├─> 3. 生成 FlinkDeployment YAML
   │      apiVersion: flink.apache.org/v1beta1
   │      kind: FlinkDeployment
   │      metadata:
   │        name: job-xxx
   │      spec:
   │        image: flink-app:latest
   │        jobManager: { memory: "1024m", cpu: 1 }
   │        taskManager: { memory: "1024m", cpu: 1, replicas: 1 }
   │        job:
   │          jarURI: local:///opt/flink/opt/flink-python-1.19.3.jar
   │          args: ["-py", "/opt/flink/usrlib/entrypoint.py"]
   │        env:
   │          - name: SCRIPT_URL
   │            value: "https://file.lemo-ai.com/xxx.py"
   │
   ├─> 4. 通过 K8s API 创建 CRD
   │      k8s_client.create_namespaced_custom_object(
   │        group="flink.apache.org",
   │        version="v1beta1",
   │        namespace="lemo-dev",
   │        plural="flinkdeployments",
   │        body=flink_deployment_yaml
   │      )
   │
   ├─> 5. Flink Operator 监听到 CRD
   │      └─> 自动创建:
   │          ├─ JobManager Pod
   │          ├─ JobManager Service
   │          ├─ TaskManager Pod(s)
   │          └─ ConfigMap (Flink 配置)
   │
   ├─> 6. Flink 作业启动
   │      ├─ JobManager 初始化
   │      ├─ TaskManager 连接到 JobManager
   │      ├─ 下载 Python 脚本 (entrypoint.py)
   │      │   └─> 从 SCRIPT_URL 下载实际脚本
   │      └─ 开始执行作业
   │
   └─> 7. 返回用户
          {
            "job_id": "job-xxx",
            "status": "RUNNING",
            "flink_job_id": "abc123..."
          }
```

### 代码调用链

```python
# 1. HTTP API
@router.post("/jobs/submit")
async def submit_job(request: FlinkJobSubmitRequest):
    job_manager = get_flink_job_manager()
    result = await job_manager.submit_job(template, request)
    return result

# 2. Job Manager
class FlinkJobManager:
    async def submit_job(self, template, request):
        # 通过 Operator 提交
        flink_job_id = await self.operator_manager.submit_job(template, request)
        return flink_job_id

# 3. Operator Job Manager
class OperatorJobManager:
    async def submit_job(self, template, request):
        # 生成 CRD YAML
        crd_yaml = self.crd_generator.generate_yaml(template, request)
        
        # 创建 CRD
        self.custom_api.create_namespaced_custom_object(
            group="flink.apache.org",
            version="v1beta1",
            namespace=self.namespace,
            plural="flinkdeployments",
            body=crd_yaml
        )
        
        return deployment_name

# 4. CRD Generator
class FlinkCRDGenerator:
    def generate_yaml(self, template, request):
        # 根据作业类型生成不同的配置
        if template.job_type == "PYTHON_SCRIPT":
            return self._generate_python_job(template, request)
        elif template.job_type == "JAR":
            return self._generate_jar_job(template, request)
        elif template.job_type == "SQL":
            return self._generate_sql_job(template, request)
```

### 支持的作业类型

#### 1. Python 脚本作业

**模板配置：**
```json
{
  "job_type": "PYTHON_SCRIPT",
  "config": {
    "script_path": "https://file.lemo-ai.com/example.py",
    "jar_files": [
      "/opt/flink/opt/flink-sql-connector-kafka-3.0.2-1.18.jar"
    ]
  }
}
```

**生成的 FlinkDeployment：**
```yaml
spec:
  job:
    jarURI: local:///opt/flink/opt/flink-python-1.19.3.jar
    entryClass: org.apache.flink.client.python.PythonDriver
    args:
      - "-py"
      - "/opt/flink/usrlib/entrypoint.py"
      - "--script-url"
      - "https://file.lemo-ai.com/example.py"
  env:
    - name: SCRIPT_URL
      value: "https://file.lemo-ai.com/example.py"
    - name: JAR_FILES
      value: "/opt/flink/opt/flink-sql-connector-kafka-3.0.2-1.18.jar"
```

#### 2. JAR 作业

**模板配置：**
```json
{
  "job_type": "JAR",
  "config": {
    "jar_path": "https://file.lemo-ai.com/my-job.jar",
    "main_class": "com.example.MainClass",
    "args": ["--config", "prod"]
  }
}
```

**生成的 FlinkDeployment：**
```yaml
spec:
  job:
    jarURI: https://file.lemo-ai.com/my-job.jar
    entryClass: com.example.MainClass
    args: ["--config", "prod"]
```

#### 3. SQL 作业

**模板配置：**
```json
{
  "job_type": "SQL",
  "config": {
    "sql": "CREATE TABLE ...; INSERT INTO ...;"
  }
}
```

**实现：** 生成一个包装 Python 脚本，使用 PyFlink Table API 执行 SQL

---

## 🔍 运维管理

### 查看作业状态

```bash
export KUBECONFIG=/root/k3s-jd-config.yaml

# 查看所有 FlinkDeployment
kubectl get flinkdeployment -n lemo-dev

# 输出示例：
# NAME                STATUS    JOB-STATUS   AGE
# job-example-py      READY     RUNNING      5m
# job-example-jar     READY     FINISHED     10m

# 查看详细信息
kubectl describe flinkdeployment job-example-py -n lemo-dev

# 查看作业 Pod
kubectl get pods -n lemo-dev -l app=job-example-py
```

### 查看作业日志

```bash
# JobManager 日志
kubectl logs -n lemo-dev -l app=job-example-py,component=jobmanager

# TaskManager 日志
kubectl logs -n lemo-dev -l app=job-example-py,component=taskmanager

# 实时跟踪
kubectl logs -f -n lemo-dev -l app=job-example-py,component=jobmanager
```

### 停止作业

**方式1: 通过前端/API**
```bash
POST /api/v1/flink/jobs/{job_id}/stop
```

**方式2: 直接删除 CRD**
```bash
kubectl delete flinkdeployment job-example-py -n lemo-dev
```

### 暂停/恢复作业（Savepoint）

```bash
# 暂停作业（创建 Savepoint）
kubectl patch flinkdeployment job-example-py -n lemo-dev \
  --type merge -p '{"spec":{"job":{"state":"suspended"}}}'

# 恢复作业（从 Savepoint）
kubectl patch flinkdeployment job-example-py -n lemo-dev \
  --type merge -p '{"spec":{"job":{"state":"running"}}}'
```

### 扩缩容

```bash
# 调整 TaskManager 副本数
kubectl patch flinkdeployment job-example-py -n lemo-dev \
  --type merge -p '{"spec":{"taskManager":{"replicas":3}}}'
```

---

## 🛠️ 故障排查

### 问题1: Operator Pod 无法启动

**症状：**
```bash
kubectl get pods -n flink-operator-system
# NAME                                     READY   STATUS             RESTARTS   AGE
# flink-kubernetes-operator-xxx            0/1     ImagePullBackOff   0          5m
```

**排查：**
```bash
# 查看 Pod 详情
kubectl describe pod -n flink-operator-system flink-kubernetes-operator-xxx

# 查看日志
kubectl logs -n flink-operator-system flink-kubernetes-operator-xxx
```

**解决：**
- 检查镜像地址是否正确
- 检查镜像仓库是否可访问
- 确认 K8s 集群可以访问 GitHub Container Registry

### 问题2: FlinkDeployment 创建失败

**症状：**
```bash
kubectl get flinkdeployment -n lemo-dev
# NAME             STATUS   ERROR
# job-example-py   FAILED   Job submission failed
```

**排查：**
```bash
# 查看 CRD 详情
kubectl describe flinkdeployment job-example-py -n lemo-dev

# 查看 Operator 日志
kubectl logs -n flink-operator-system -l app.kubernetes.io/name=flink-kubernetes-operator
```

**常见原因：**
1. 镜像拉取失败 → 检查镜像地址和拉取凭证
2. 资源不足 → 检查 K8s 节点资源
3. RBAC 权限不足 → 检查 ServiceAccount 权限
4. 配置错误 → 检查 CRD YAML 语法

### 问题3: 作业启动后立即失败

**症状：**
```bash
kubectl get pods -n lemo-dev -l app=job-example-py
# NAME                     READY   STATUS       RESTARTS   AGE
# job-example-py-jm-xxx    0/1     Error        0          1m
```

**排查：**
```bash
# 查看 JobManager 日志
kubectl logs -n lemo-dev job-example-py-jm-xxx

# 常见错误：
# 1. Python 脚本下载失败
# 2. JAR 依赖找不到
# 3. Kafka/MongoDB/Redis 连接失败
# 4. Python 代码语法错误
```

**解决：**
```bash
# 1. 检查脚本 URL 是否可访问
curl -I https://file.lemo-ai.com/example.py

# 2. 检查 JAR 文件是否存在
kubectl exec -it job-example-py-tm-xxx -n lemo-dev -- \
  ls -l /opt/flink/opt/

# 3. 检查网络连接
kubectl exec -it job-example-py-tm-xxx -n lemo-dev -- \
  curl -v 111.228.39.41:9092
```

### 问题4: gRPC 服务报 ModuleNotFoundError

**症状：**
```
ModuleNotFoundError: No module named 'app.utils.logger'
```

**解决：**
- 确保 `operator_job_manager.py` 使用 `from loguru import logger`
- 重新构建并部署服务

---

##  📚 参考资料

- **Flink Kubernetes Operator 官方文档**: https://nightlies.apache.org/flink/flink-kubernetes-operator-docs-main/
- **Flink 官方文档**: https://nightlies.apache.org/flink/flink-docs-release-1.19/
- **Kubernetes CRD 文档**: https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/
- **项目 GitHub**: https://github.com/AndrewLiuZhangZong/lemo_recommender

---

## 📝 快速参考

### 常用命令

```bash
# 设置 kubeconfig
export KUBECONFIG=/root/k3s-jd-config.yaml

# 查看 Operator
kubectl get pods -n flink-operator-system

# 查看推荐服务
kubectl get pods -n lemo-dev | grep lemo-service-recommender

# 查看所有 Flink 作业
kubectl get flinkdeployment -n lemo-dev

# 查看作业详情
kubectl describe flinkdeployment <job-name> -n lemo-dev

# 查看作业日志
kubectl logs -f -l app=<job-name>,component=jobmanager -n lemo-dev

# 删除作业
kubectl delete flinkdeployment <job-name> -n lemo-dev

# 重启推荐服务
kubectl rollout restart deployment/lemo-service-recommender-http -n lemo-dev
```

### 配置文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| Operator 安装脚本 | `scripts/install_flink_operator.sh` | 安装 Flink Operator |
| 服务部署脚本 | `k8s-deploy/deploy-*.sh` | 部署推荐服务 |
| K8s 配置 | `k8s-deploy/k8s-deployment-*.yaml` | K8s 部署清单 |
| kubeconfig | `k8s-deploy/k3s-jd-config.yaml` | K8s 集群配置 |
| Job Manager | `app/services/flink/job_manager.py` | 作业管理核心逻辑 |
| Operator Manager | `app/services/flink/operator_job_manager.py` | Operator 集成 |
| CRD Generator | `app/services/flink/crd_generator.py` | CRD YAML 生成 |

---

**文档版本**: v1.0  
**更新时间**: 2025-11-03  
**维护者**: Lemo 推荐系统团队


