# Flink Kubernetes Operator 迁移方案

## 一、方案概述

### 当前架构（方案B）
- Session 集群 + K8s Job 提交
- Python 服务通过 K8s Job 调用 `flink run` 命令
- 需要 `host_network` 访问外网 Flink

### 目标架构（方案A）
- Flink Kubernetes Operator + Application Mode
- 通过 CRD 声明式管理作业
- 每个作业独立 Flink 集群（JobManager + TaskManager）

---

## 二、迁移步骤

### 阶段1：准备工作（预计1小时）

#### 1.1 安装 Flink Kubernetes Operator

```bash
# 1. 安装 cert-manager（Operator 依赖）
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.8.2/cert-manager.yaml

# 2. 安装 Flink Kubernetes Operator
kubectl create namespace flink-operator-system

helm repo add flink-operator-repo https://downloads.apache.org/flink/flink-kubernetes-operator-1.7.0/
helm install flink-kubernetes-operator flink-operator-repo/flink-kubernetes-operator \
  --namespace flink-operator-system
```

#### 1.2 验证 Operator 安装

```bash
# 检查 Operator Pod 状态
kubectl get pods -n flink-operator-system

# 检查 CRD 是否安装
kubectl get crd | grep flink
# 应该看到: flinkdeployments.flink.apache.org
```

#### 1.3 构建 Application Mode 镜像

创建新的 Dockerfile，将 Python 脚本打包到镜像中。

**文件位置**: `Dockerfile.flink-app`

```dockerfile
# 基于 Flink Python 镜像
FROM registry.cn-beijing.aliyuncs.com/lemo_zls/flink-python:latest

# 设置工作目录
WORKDIR /opt/flink/usrlib

# 安装额外的 Python 依赖（如果需要）
RUN pip3 install --no-cache-dir requests pyyaml

# 将脚本下载入口点添加到镜像
COPY scripts/flink_app_entrypoint.py /opt/flink/usrlib/entrypoint.py

# 设置环境变量
ENV PYFLINK_CLIENT_EXECUTABLE=python3
ENV PYFLINK_EXECUTABLE=python3

# 容器启动命令将由 Flink Operator 控制
```

---

### 阶段2：代码改造（预计2-3小时）

#### 2.1 创建 Flink 作业提交服务

**文件位置**: `app/services/flink/operator_job_manager.py`

功能：
- 读取作业模板
- 生成 FlinkDeployment CRD YAML
- 通过 K8s API 创建/删除 CRD
- 监控作业状态

#### 2.2 创建 CRD 模板生成器

**文件位置**: `app/services/flink/crd_generator.py`

功能：
- 根据作业模板生成 FlinkDeployment YAML
- 支持动态参数注入（脚本 URL、JAR 依赖等）
- 配置 JobManager 和 TaskManager 资源

#### 2.3 修改作业提交逻辑

**文件位置**: `app/services/flink/job_manager.py`

改造：
- 添加新的 `_submit_via_operator()` 方法
- 保留原有 `_submit_python_script()` 作为降级方案
- 通过配置开关控制使用哪种提交方式

#### 2.4 添加 Python 脚本下载入口点

**文件位置**: `scripts/flink_app_entrypoint.py`

功能：
- 从环境变量读取脚本 URL
- 下载脚本到本地
- 下载 JAR 依赖
- 执行 Python 脚本

---

### 阶段3：配置管理（预计1小时）

#### 3.1 添加配置项

**文件位置**: `app/core/config.py`

```python
# Flink 提交模式配置
flink_submit_mode: str = Field(default="operator", description="Flink 作业提交模式: operator 或 session")
flink_operator_namespace: str = Field(default="lemo-dev", description="Flink Operator 命名空间")
flink_app_image: str = Field(default="registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest")
```

#### 3.2 K8s ConfigMap 更新

**文件位置**: `k8s-deploy/k8s-deployment-http-grpc.yaml`

添加：
```yaml
FLINK_SUBMIT_MODE: "operator"
FLINK_OPERATOR_NAMESPACE: "lemo-dev"
FLINK_APP_IMAGE: "registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest"
```

---

### 阶段4：RBAC 权限配置（预计30分钟）

#### 4.1 更新 ServiceAccount 权限

**文件位置**: `k8s-deploy/k8s-deployment-http-grpc.yaml`

添加 FlinkDeployment CRD 权限：

```yaml
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: lemo-service-recommender-flink-operator-role
  namespace: lemo-dev
rules:
  # FlinkDeployment CRD 权限
  - apiGroups: ["flink.apache.org"]
    resources: ["flinkdeployments"]
    verbs: ["create", "get", "list", "watch", "update", "patch", "delete"]
  - apiGroups: ["flink.apache.org"]
    resources: ["flinkdeployments/status"]
    verbs: ["get", "list", "watch"]
  # 原有权限保留...
```

---

### 阶段5：部署与测试（预计2小时）

#### 5.1 构建并推送镜像

```bash
# 构建 Application Mode 镜像
docker build -f Dockerfile.flink-app -t registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest .

# 推送到 ACR
docker push registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest
```

#### 5.2 部署推荐服务

```bash
# 更新 ConfigMap
kubectl apply -f k8s-deploy/k8s-deployment-http-grpc.yaml

# 重启服务
kubectl rollout restart deployment/lemo-service-recommender-http -n lemo-dev
kubectl rollout restart deployment/lemo-service-recommender-grpc -n lemo-dev
```

#### 5.3 测试作业提交

1. 在前端创建一个测试作业模板
2. 提交作业
3. 查看 FlinkDeployment 状态：
   ```bash
   kubectl get flinkdeployment -n lemo-dev
   kubectl describe flinkdeployment <job-name> -n lemo-dev
   ```
4. 查看作业 Pod：
   ```bash
   kubectl get pods -n lemo-dev -l app=<job-name>
   ```

---

## 三、灰度迁移策略

### 3.1 双模式并存

- 保留 Session 集群和 K8s Job 提交方式
- 通过配置 `FLINK_SUBMIT_MODE` 控制提交方式
- 默认使用 `operator` 模式，失败时降级到 `session` 模式

### 3.2 逐步迁移

**第1周**：测试环境试运行
- 仅在测试环境启用 Operator 模式
- 验证功能完整性和稳定性

**第2周**：生产环境小流量
- 生产环境启用 Operator 模式
- 仅迁移10%的作业
- 监控性能和错误率

**第3周**：全量迁移
- 迁移所有作业到 Operator 模式
- Session 集群保留1周作为降级方案

**第4周**：下线 Session 集群
- 确认无问题后，下线 Session 集群
- 清理 K8s Job 相关代码

---

## 四、关键技术点

### 4.1 FlinkDeployment CRD 示例

```yaml
apiVersion: flink.apache.org/v1beta1
kind: FlinkDeployment
metadata:
  name: example-python-job
  namespace: lemo-dev
spec:
  image: registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest
  flinkVersion: v1_19
  flinkConfiguration:
    taskmanager.numberOfTaskSlots: "2"
    python.client.executable: python3
    python.executable: python3
  serviceAccount: lemo-service-recommender-sa
  jobManager:
    resource:
      memory: "1024m"
      cpu: 1
  taskManager:
    resource:
      memory: "1024m"
      cpu: 1
    replicas: 1
  job:
    jarURI: local:///opt/flink/opt/flink-python-1.19.3.jar
    entryClass: org.apache.flink.client.python.PythonDriver
    args: 
      - "-py"
      - "/opt/flink/usrlib/entrypoint.py"
      - "--script-url"
      - "https://file.lemo-ai.com/2025/11/01/example.py"
    parallelism: 2
    upgradeMode: stateless
  env:
    - name: SCRIPT_URL
      value: "https://file.lemo-ai.com/2025/11/01/example.py"
    - name: KAFKA_SERVERS
      value: "111.228.39.41:9092"
```

### 4.2 Python 脚本下载入口点

```python
#!/usr/bin/env python3
import os
import sys
import urllib.request

# 从环境变量读取脚本 URL
script_url = os.environ.get('SCRIPT_URL')
if not script_url:
    print("错误: 未设置 SCRIPT_URL 环境变量")
    sys.exit(1)

# 下载脚本
print(f"下载脚本: {script_url}")
script_path = "/tmp/user_script.py"
urllib.request.urlretrieve(script_url, script_path)

# 执行脚本
print(f"执行脚本: {script_path}")
exec(open(script_path).read())
```

---

## 五、回滚方案

如果 Operator 模式出现问题，可以快速回滚：

```bash
# 1. 切换配置为 Session 模式
kubectl set env deployment/lemo-service-recommender-http -n lemo-dev FLINK_SUBMIT_MODE=session

# 2. 重启服务
kubectl rollout restart deployment/lemo-service-recommender-http -n lemo-dev

# 3. 删除所有 FlinkDeployment
kubectl delete flinkdeployment --all -n lemo-dev
```

---

## 六、监控指标

### 6.1 关键指标

- FlinkDeployment 创建成功率
- 作业启动时间（从提交到 RUNNING）
- 作业失败率
- 资源利用率（CPU、内存）
- Pod 重启次数

### 6.2 告警规则

- FlinkDeployment 创建失败 > 5% 触发告警
- 作业启动时间 > 5分钟 触发告警
- Pod 频繁重启（10分钟内重启 > 3次）触发告警

---

## 七、常见问题

### Q1: Operator 和 Session 模式有什么区别？

| 特性 | Operator (Application) | Session (K8s Job) |
|------|----------------------|-------------------|
| 资源隔离 | ✅ 独立集群 | ❌ 共享集群 |
| 启动时间 | 🔴 较慢（1-2分钟） | 🟢 较快（10-30秒） |
| 资源利用 | ✅ 按需分配 | ❌ 需预留资源 |
| 运维复杂度 | 🟢 自动化 | 🔴 手动管理 |

### Q2: 如何处理长时间运行的作业？

Application Mode 天然支持长时间运行，Operator 会自动管理 Checkpoint、Savepoint 和故障恢复。

### Q3: 迁移过程中会影响现有作业吗？

不会。迁移采用双模式并存，现有作业继续在 Session 集群运行，新作业使用 Operator 提交。

---

## 八、时间估算

| 阶段 | 预计时间 | 备注 |
|------|---------|------|
| 安装 Operator | 1小时 | 包括验证 |
| 代码改造 | 2-3小时 | 核心开发工作 |
| 配置管理 | 1小时 | ConfigMap、RBAC |
| 部署测试 | 2小时 | 包括灰度测试 |
| **总计** | **6-7小时** | 1个工作日完成 |

---

## 九、下一步行动

1. ✅ 阅读并确认迁移方案
2. ⏳ 执行阶段1：安装 Flink Kubernetes Operator
3. ⏳ 执行阶段2：代码改造
4. ⏳ 执行阶段3-5：配置、部署、测试
5. ⏳ 灰度迁移并监控
6. ⏳ 全量上线并下线 Session 集群

---

**准备好开始了吗？我们从阶段1开始！** 🚀

