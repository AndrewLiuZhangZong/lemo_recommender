# Flink Python 和 SQL 作业支持配置指南

## 📋 概述

本文档介绍如何在已部署的 Flink 集群中启用 Python 和 SQL 作业支持。

**当前状态：**
- ✅ Flink 集群已部署（Docker/K8s）
- ❌ 不支持 Python 作业
- ❌ 不支持 SQL 作业

**目标：**
- ✅ 支持 PyFlink 作业提交
- ✅ 支持 Flink SQL 作业提交

---

## 🐍 方案一：启用 PyFlink 支持

### 1.1 了解 PyFlink

PyFlink 是 Flink 的 Python API，允许使用 Python 编写 Flink 作业。

**架构：**
```
用户 Python 脚本
    ↓
PyFlink API
    ↓
Flink Python Runtime (Java Process)
    ↓
Flink JobManager/TaskManager
```

### 1.2 环境要求

- Python 3.7, 3.8, 3.9, 或 3.10
- Java 11 或 Java 8
- Apache Flink 1.19.x

### 1.3 Docker 镜像配置

**方式 A：使用官方 Flink Python 镜像**

修改 `docker-compose.yml`：

```yaml
flink:
  # 使用包含 Python 支持的镜像
  image: flink:1.19-scala_2.12-java11-python
  # 或者自定义构建
  # build:
  #   context: .
  #   dockerfile: Dockerfile.flink-python
  ...
```

**方式 B：自定义 Dockerfile（推荐）**

创建 `Dockerfile.flink-python`：

```dockerfile
FROM flink:1.19-scala_2.12-java11

# 安装 Python 和依赖
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-dev && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*

# 安装 PyFlink
RUN pip3 install --no-cache-dir apache-flink==1.19.0

# 安装常用 Python 库
RUN pip3 install --no-cache-dir \
    pandas \
    numpy \
    kafka-python \
    pymongo \
    redis

# 创建作业目录
RUN mkdir -p /opt/flink/usrlib

WORKDIR /opt/flink
```

构建镜像：

```bash
docker build -f Dockerfile.flink-python -t flink-python:1.19 .
```

更新 `docker-compose.yml`：

```yaml
flink:
  image: flink-python:1.19
  volumes:
    - ./flink_jobs:/opt/flink/usrlib  # 挂载作业目录
  ...
```

### 1.4 K8s 部署配置

修改 `k8s-deploy/k8s-deployment-http-grpc.yaml` 中的 Flink 配置：

```yaml
# 添加 Flink Python 环境配置
apiVersion: v1
kind: ConfigMap
metadata:
  name: flink-python-config
  namespace: lemo-dev
data:
  # Python 环境配置
  PYTHON_VERSION: "3.9"
  PYFLINK_CLIENT_EXECUTABLE: "python3"
---
# 可选：创建 Flink Python 作业的 PVC
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: flink-python-jobs
  namespace: lemo-dev
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
```

### 1.5 提交 Python 作业的方式

#### 方式 1：通过 CLI 命令（推荐）

在 Flink JobManager Pod 中执行：

```bash
# 进入 Flink JobManager Pod
kubectl exec -it <flink-jobmanager-pod> -n lemo-dev -- /bin/bash

# 提交 Python 作业
flink run -py /opt/flink/usrlib/my_job.py \
    --jarfile /opt/flink/opt/flink-python_*.jar \
    --parallelism 2

# 带依赖的作业
flink run -py /opt/flink/usrlib/my_job.py \
    --pyFiles file:///opt/flink/usrlib/utils.py,file:///opt/flink/usrlib/config.py \
    --pyArchives /opt/flink/usrlib/venv.zip#venv \
    --parallelism 2
```

#### 方式 2：通过 REST API（需要额外处理）

Flink REST API 不直接支持 Python 脚本，需要：

**步骤 1：** 将 Python 脚本和依赖打包成 ZIP

```bash
# 创建工作目录
mkdir -p my_job
cd my_job

# 复制脚本
cp my_job.py .

# 安装依赖到本地
pip install -r requirements.txt -t ./packages

# 打包
zip -r my_job.zip my_job.py packages/
```

**步骤 2：** 上传 ZIP 到 Flink（将 ZIP 当作 JAR 上传）

```bash
curl -X POST -H "Expect:" \
    -F "jarfile=@my_job.zip" \
    http://flink-jobmanager:8081/jars/upload
```

**步骤 3：** 运行作业

```bash
curl -X POST \
    http://flink-jobmanager:8081/jars/<jar-id>/run \
    -H "Content-Type: application/json" \
    -d '{
        "programArgs": "-py my_job.py",
        "parallelism": 2
    }'
```

#### 方式 3：通过 Kubernetes Job（推荐用于我们的场景）

创建 K8s Job 来提交 Flink 作业：

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: flink-python-job-{{ job_id }}
  namespace: lemo-dev
spec:
  template:
    spec:
      containers:
      - name: flink-submitter
        image: flink-python:1.19
        command:
        - /bin/bash
        - -c
        - |
          # 下载 Python 脚本（从 OSS）
          wget -O /tmp/job.py {{ script_url }}
          
          # 提交到 Flink 集群
          flink run \
            -m {{ flink_jobmanager_address }}:8081 \
            -py /tmp/job.py \
            --parallelism {{ parallelism }}
        env:
        - name: FLINK_REST_URL
          value: "http://flink-jobmanager:8081"
      restartPolicy: Never
```

---

## 🗃️ 方案二：启用 Flink SQL 支持

### 2.1 了解 Flink SQL

Flink SQL 允许使用标准 SQL 语句进行流式和批处理。

**组件：**
- **Flink SQL Client**: 交互式 SQL 命令行工具
- **Flink SQL Gateway**: REST API 服务（推荐）

### 2.2 方式 A：使用 Flink SQL Client（简单）

#### 安装配置

Flink 已内置 SQL Client，直接使用：

```bash
# 进入 Flink JobManager Pod
kubectl exec -it <flink-jobmanager-pod> -n lemo-dev -- /bin/bash

# 启动 SQL Client
./bin/sql-client.sh
```

#### 提交 SQL 作业

**方式 1：交互式**

```sql
-- 在 SQL Client 中执行
CREATE TABLE my_table (
    id INT,
    name STRING,
    created_at TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'my-topic',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json'
);

INSERT INTO my_table VALUES (1, 'test', NOW());
```

**方式 2：执行 SQL 文件**

```bash
# 准备 SQL 文件
cat > /tmp/my_job.sql << EOF
CREATE TABLE ...;
INSERT INTO ...;
EOF

# 执行
./bin/sql-client.sh -f /tmp/my_job.sql
```

### 2.3 方式 B：使用 Flink SQL Gateway（推荐）

SQL Gateway 提供 REST API，适合程序化调用。

#### 部署 SQL Gateway

**Docker Compose 方式：**

修改 `docker-compose.yml`：

```yaml
services:
  flink-sql-gateway:
    image: flink:1.19-scala_2.12-java11
    container_name: flink-sql-gateway
    command: >
      bash -c "
      ./bin/sql-gateway.sh start -Dsql-gateway.endpoint.rest.address=0.0.0.0 &&
      tail -f /opt/flink/log/flink-*-sql-gateway-*.log
      "
    ports:
      - "8083:8083"  # SQL Gateway REST API
    environment:
      FLINK_PROPERTIES: |
        jobmanager.rpc.address: flink
        sql-gateway.endpoint.rest.address: 0.0.0.0
        sql-gateway.endpoint.rest.port: 8083
    networks:
      - lemo-network
    depends_on:
      - flink
```

**Kubernetes 方式：**

创建 `k8s-deploy/flink-sql-gateway-deployment.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flink-sql-gateway
  namespace: lemo-dev
spec:
  replicas: 1
  selector:
    matchLabels:
      app: flink-sql-gateway
  template:
    metadata:
      labels:
        app: flink-sql-gateway
    spec:
      containers:
      - name: sql-gateway
        image: flink:1.19-scala_2.12-java11
        command:
        - /bin/bash
        - -c
        - |
          ./bin/sql-gateway.sh start \
            -Dsql-gateway.endpoint.rest.address=0.0.0.0 \
            -Djobmanager.rpc.address=flink-jobmanager &&
          tail -f /opt/flink/log/*.log
        ports:
        - containerPort: 8083
          name: rest
        env:
        - name: FLINK_PROPERTIES
          value: |
            jobmanager.rpc.address: flink-jobmanager
            sql-gateway.endpoint.rest.address: 0.0.0.0
            sql-gateway.endpoint.rest.port: 8083
---
apiVersion: v1
kind: Service
metadata:
  name: flink-sql-gateway
  namespace: lemo-dev
spec:
  selector:
    app: flink-sql-gateway
  ports:
  - port: 8083
    targetPort: 8083
    name: rest
```

部署：

```bash
kubectl apply -f k8s-deploy/flink-sql-gateway-deployment.yaml
```

#### 使用 SQL Gateway API

**创建会话：**

```bash
curl -X POST http://flink-sql-gateway:8083/v1/sessions \
    -H "Content-Type: application/json" \
    -d '{
        "properties": {
            "execution.runtime-mode": "streaming"
        }
    }'

# 返回：{"sessionHandle":"..."}
```

**执行 SQL：**

```bash
SESSION_HANDLE="<从上面获取>"

curl -X POST http://flink-sql-gateway:8083/v1/sessions/$SESSION_HANDLE/statements \
    -H "Content-Type: application/json" \
    -d '{
        "statement": "CREATE TABLE my_table ...; INSERT INTO my_table ...;"
    }'
```

**查询结果：**

```bash
OPERATION_HANDLE="<从执行返回>"

curl -X GET http://flink-sql-gateway:8083/v1/sessions/$SESSION_HANDLE/operations/$OPERATION_HANDLE/result/0
```

---

## 🔧 在推荐系统中集成

### 3.1 更新后端代码

修改 `app/services/flink/job_manager.py`：

```python
async def _submit_python_script(self, template: JobTemplate, request: FlinkJobSubmitRequest) -> str:
    """
    通过 Kubernetes Job 提交 Python 作业
    """
    script_path = template.config.get("script_path")
    parallelism = request.job_config.get("parallelism", template.parallelism)
    
    # 创建 K8s Job
    job_manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": f"flink-python-{request.job_id}",
            "namespace": "lemo-dev"
        },
        "spec": {
            "template": {
                "spec": {
                    "containers": [{
                        "name": "flink-submitter",
                        "image": "flink-python:1.19",
                        "command": [
                            "/bin/bash",
                            "-c",
                            f"""
                            wget -O /tmp/job.py {script_path}
                            flink run -m {self.flink_rest_url.replace('http://', '').replace(':8081', '')}:8081 \
                                -py /tmp/job.py \
                                --parallelism {parallelism}
                            """
                        ]
                    }],
                    "restartPolicy": "Never"
                }
            }
        }
    }
    
    # 使用 Kubernetes API 创建 Job
    from kubernetes import client, config
    config.load_incluster_config()  # 在 K8s Pod 中运行
    
    batch_api = client.BatchV1Api()
    batch_api.create_namespaced_job(
        namespace="lemo-dev",
        body=job_manifest
    )
    
    logger.info(f"已创建 K8s Job: flink-python-{request.job_id}")
    return request.job_id


async def _submit_sql(self, template: JobTemplate, request: FlinkJobSubmitRequest) -> str:
    """
    通过 SQL Gateway 提交 SQL 作业
    """
    sql = template.config.get("sql")
    
    # 1. 创建 SQL Gateway 会话
    session_response = await self.client.post(
        f"{self.sql_gateway_url}/v1/sessions",
        json={
            "properties": {
                "execution.runtime-mode": "streaming"
            }
        }
    )
    session_handle = session_response.json()["sessionHandle"]
    
    # 2. 执行 SQL
    stmt_response = await self.client.post(
        f"{self.sql_gateway_url}/v1/sessions/{session_handle}/statements",
        json={"statement": sql}
    )
    operation_handle = stmt_response.json()["operationHandle"]
    
    logger.info(f"SQL 作业已提交: session={session_handle}, operation={operation_handle}")
    return operation_handle
```

### 3.2 更新配置

修改 `app/core/config.py`：

```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # Flink 配置
    flink_rest_url: str = "http://111.228.39.41:8081"
    flink_sql_gateway_url: str = "http://flink-sql-gateway:8083"  # 新增
    
    # Kubernetes 配置（用于创建 Job）
    k8s_namespace: str = "lemo-dev"
    k8s_in_cluster: bool = True  # 是否在 K8s 集群内运行
```

### 3.3 添加 Python 依赖

修改 `pyproject.toml`：

```toml
[tool.poetry.dependencies]
# ... 现有依赖 ...
kubernetes = "^28.1.0"  # K8s API 客户端
```

安装：

```bash
poetry add kubernetes
```

---

## 📊 测试验证

### 4.1 测试 PyFlink 支持

**创建测试脚本** `test_pyflink.py`：

```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.typeinfo import Types
from pyflink.datastream.functions import MapFunction

class MyMapFunction(MapFunction):
    def map(self, value):
        return value * 2

def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    
    data = env.from_collection([1, 2, 3, 4, 5], type_info=Types.INT())
    data.map(MyMapFunction()).print()
    
    env.execute("PyFlink Test Job")

if __name__ == '__main__':
    main()
```

**提交测试：**

```bash
# 进入 Flink Pod
kubectl exec -it <flink-jobmanager-pod> -n lemo-dev -- /bin/bash

# 执行
flink run -py /tmp/test_pyflink.py
```

### 4.2 测试 SQL Gateway

```bash
# 创建会话
curl -X POST http://flink-sql-gateway:8083/v1/sessions

# 执行简单 SQL
curl -X POST http://flink-sql-gateway:8083/v1/sessions/<session-handle>/statements \
    -H "Content-Type: application/json" \
    -d '{"statement": "SELECT 1"}'
```

---

## 🎯 推荐实施步骤

### 阶段 1：基础环境准备（1-2 天）

1. ✅ 构建 Flink Python 镜像
2. ✅ 更新 Docker Compose / K8s 配置
3. ✅ 验证 PyFlink 基础功能

### 阶段 2：Python 作业支持（2-3 天）

1. ✅ 实现 K8s Job 提交方式
2. ✅ 更新后端 API
3. ✅ 测试端到端流程
4. ✅ 更新前端界面

### 阶段 3：SQL Gateway 集成（2-3 天）

1. ✅ 部署 SQL Gateway
2. ✅ 实现 SQL 作业提交
3. ✅ 添加 SQL 编辑器（前端）
4. ✅ 测试验证

### 阶段 4：生产优化（持续）

1. ✅ 依赖管理优化
2. ✅ 作业监控告警
3. ✅ 性能调优
4. ✅ 文档完善

---

## 📚 参考资料

- [Apache Flink Python API 官方文档](https://nightlies.apache.org/flink/flink-docs-release-1.19/docs/dev/python/overview/)
- [Flink SQL Gateway 文档](https://nightlies.apache.org/flink/flink-docs-release-1.19/docs/dev/table/sql-gateway/overview/)
- [PyFlink 安装指南](https://nightlies.apache.org/flink/flink-docs-release-1.19/docs/dev/python/installation/)
- [Flink Kubernetes Operator](https://nightlies.apache.org/flink/flink-kubernetes-operator-docs-main/)

---

## ❓ 常见问题

### Q1: 为什么不能直接上传 Python 脚本到 `/jars/upload`？

**A:** Flink REST API 的 `/jars/upload` 端点设计用于 JAR 文件。Python 脚本需要通过 CLI 工具（`flink run -py`）或打包成特殊格式才能提交。

### Q2: Python 依赖怎么管理？

**A:** 三种方式：
1. 在 Flink 镜像中预装常用库
2. 使用 `--pyArchives` 上传虚拟环境 ZIP
3. 使用 `--pyRequirements` 指定 requirements.txt

### Q3: SQL Gateway 是必需的吗？

**A:** 不是。如果只需要基础 SQL 功能，可以使用 SQL Client。SQL Gateway 提供 REST API，适合程序化集成。

### Q4: 性能会受影响吗？

**A:** PyFlink 使用 Python UDF 时会有额外开销。纯 SQL 或 Java/Scala 作业性能更好。建议：
- 计算密集型任务用 Java/Scala
- 数据处理和业务逻辑用 Python
- 简单查询用 SQL

---

**文档版本：** v1.0  
**更新时间：** 2025-11-01  
**维护者：** 推荐系统团队

