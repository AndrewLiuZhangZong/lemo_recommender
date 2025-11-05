# Flink 架构完整梳理（企业级标准）

## 📋 当前状态检查清单

### ✅ 1. 版本配置
- **Flink 运行时**: 2.0.0 (最新稳定版)
- **PyFlink**: 2.1.1 (最新稳定版)
- **Kafka Connector**: 3.3.0-2.0
- **Scala 版本**: 2.12
- **Java 版本**: 11

### ✅ 2. 镜像架构
```
flink:2.0-scala_2.12-java11
  ↓ (基础镜像)
flink-python:latest
  ├─ Python 3.11
  ├─ apache-flink==2.1.1 ← 关键！必须安装
  ├─ pandas, numpy, protobuf
  └─ Kafka Connector JAR
  ↓
flink-app:latest
  ├─ 继承 flink-python
  └─ entrypoint.py (脚本下载器)
```

### ✅ 3. CRD 配置
- **flinkVersion**: v2_0
- **jarURI**: `flink-python_2.12-2.0.0.jar`
- **entryClass**: `org.apache.flink.client.python.PythonDriver`

### 🔍 4. 关键问题排查

#### 问题1: TaskManager 缺少 pyflink 模块
**根本原因**: `Dockerfile.flink-python` 之前**没有安装** `apache-flink` Python 包

**业界标准**:
- Flink 官方镜像只包含 Java 运行时
- Python API (PyFlink) 需要单独通过 `pip install apache-flink` 安装
- 版本必须严格匹配：Flink 2.0.x ↔ PyFlink 2.1.x

**修复**:
```dockerfile
RUN pip3 install --no-cache-dir apache-flink==2.1.1
```

#### 问题2: 版本配置不一致
**原因**: 代码中硬编码了多个版本号

**修复**:
1. `Dockerfile.flink-python`: FROM flink:2.0, apache-flink==2.1.1
2. `crd_generator.py`: flinkVersion: v2_0, jarURI 使用正确文件名
3. 文档同步更新

### 📦 5. 构建流程

#### 步骤1: 构建 flink-python (基础镜像)
```bash
docker buildx build --platform linux/amd64 \
  -t registry.cn-beijing.aliyuncs.com/lemo_zls/flink-python:latest \
  -f Dockerfile.flink-python \
  --push .
```

**验证**:
```bash
docker run --rm registry.cn-beijing.aliyuncs.com/lemo_zls/flink-python:latest \
  python3 -c "import pyflink; print(f'PyFlink: {pyflink.__version__}')"
# 预期输出: PyFlink: 2.1.1
```

#### 步骤2: 构建 flink-app (应用镜像)
```bash
docker buildx build --platform linux/amd64 \
  -t registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest \
  -f Dockerfile.flink-app \
  --push .
```

**验证**:
```bash
docker run --rm registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest \
  python3 -c "import pyflink; print(f'PyFlink: {pyflink.__version__}')"
# 预期输出: PyFlink: 2.1.1

docker run --rm registry.cn-beijing.aliyuncs.com/lemo_zls/flink-app:latest \
  ls -lh /opt/flink/usrlib/entrypoint.py
# 预期: 应该存在 entrypoint.py
```

#### 步骤3: 重启服务
```bash
export KUBECONFIG=/path/to/k3s-jd-config.yaml
kubectl rollout restart deployment/lemo-service-recommender-http -n lemo-dev
kubectl rollout restart deployment/lemo-service-recommender-grpc -n lemo-dev
```

#### 步骤4: 提交测试作业
使用前端提交 `minimal_test.py`，验证 TaskManager 可以正常找到 `pyflink` 模块

### 🏢 6. 企业级标准对照

#### 阿里云实时计算 Flink
- ✅ 分层镜像架构 (base → python → app)
- ✅ 版本严格锁定
- ✅ 预定义资源档位 (micro/small/medium/large/xlarge)
- ✅ 自动伸缩 (HPA + Reactive Mode)

#### 字节跳动 Flink 实践
- ✅ Flink Kubernetes Operator
- ✅ Application Mode (作业隔离)
- ✅ 自动化测试 + 灰度发布
- ✅ 监控告警完整闭环

#### AWS EMR Flink
- ✅ PyFlink 作为必需依赖
- ✅ 资源按需分配
- ✅ 完整的日志/监控集成

### ✅ 7. 我们的实现对照

| 特性 | 阿里云 | 字节 | AWS | 我们 | 状态 |
|------|--------|------|-----|------|------|
| 分层镜像 | ✅ | ✅ | ✅ | ✅ | ✅ 已实现 |
| 版本锁定 | ✅ | ✅ | ✅ | ✅ | ✅ 已实现 |
| PyFlink 安装 | ✅ | ✅ | ✅ | ✅ | ✅ 已修复 |
| Operator 模式 | ✅ | ✅ | ❌ | ✅ | ✅ 已实现 |
| 资源档位 | ✅ | ❌ | ✅ | ✅ | ✅ 已实现 |
| HPA | ✅ | ✅ | ✅ | ✅ | ✅ 已实现 |
| Reactive Mode | ✅ | ✅ | ❌ | ✅ | ✅ 已实现 |
| 定时伸缩 | ❌ | ✅ | ❌ | ✅ | ✅ 已实现 |
| 多作业类型 | ✅ | ✅ | ✅ | ✅ | ✅ Python/JAR/SQL |

### 🎯 8. 下一步操作

1. ✅ 代码已修复并推送
2. 🔄 构建新镜像 (flink-python → flink-app)
3. 🔄 重启服务
4. 🔄 提交测试作业验证

---
**文档版本**: v1.0  
**更新时间**: 2025-11-04  
**状态**: 准备构建镜像
