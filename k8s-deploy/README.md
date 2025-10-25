# Lemo Recommender K8s 部署指南

## 📋 部署说明

本目录包含了推荐服务部署到 K3s 集群的相关配置和脚本。

## 🗂️ 文件说明

- `deploy-to-k3s.sh` - 一键部署脚本
- `k8s-deployment.yaml` - Kubernetes 部署配置文件
- `k3s-jd-config.yaml` - K3s 集群配置文件

## 🚀 部署步骤

### 1. 前置条件

- Docker 已安装并运行
- 可访问阿里云容器镜像服务（ACR）
- K3s 集群已配置并可访问

### 2. 执行部署

```bash
cd /Users/a123/Lemo/lemo_recommender
./k8s-deploy/deploy-to-k3s.sh
```

### 3. 部署流程

脚本会自动执行以下步骤：

1. **构建 Docker 镜像** - 基于当前代码构建镜像
2. **登录 ACR** - 登录阿里云容器镜像服务
3. **推送镜像** - 将镜像推送到 ACR
4. **删除旧服务** - 删除可能存在的旧服务（避免冲突）
5. **应用配置** - 部署到 K3s 集群

## 📦 部署内容

### 服务组件

1. **HTTP API Server** (2 副本)
   - 端口：8000 (HTTP API)
   - 端口：9090 (Prometheus Metrics)
   - NodePort：30801 (HTTP), 30802 (Metrics)

2. **gRPC Server** (2 副本)
   - 端口：50051 (gRPC)
   - 服务名：`lemo-service-recommender`
   - ClusterIP 类型（集群内访问）

### 配置资源

- **ConfigMap**: `lemo-service-recommender-config`
  - 包含所有环境变量配置
  - MongoDB、Redis、Kafka、Milvus 连接信息

- **ServiceAccount**: `lemo-service-recommender-sa`
- **Role & RoleBinding**: 授予必要的 K8s 权限

## 🔍 验证部署

### 查看 Pods 状态

```bash
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get pods -l app=lemo-service-recommender
```

### 查看服务状态

```bash
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev get svc -l app=lemo-service-recommender
```

### 查看 HTTP API 日志

```bash
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev logs -f deployment/lemo-service-recommender-http
```

### 查看 gRPC Server 日志

```bash
kubectl --kubeconfig=k8s-deploy/k8s-jd-config.yaml -n lemo-dev logs -f deployment/lemo-service-recommender-grpc
```

## 🌐 访问服务

### HTTP API

- **集群外访问**: `http://<K3s-Node-IP>:30801`
- **健康检查**: `http://<K3s-Node-IP>:30801/health`
- **API 文档**: `http://<K3s-Node-IP>:30801/docs`
- **Prometheus**: `http://<K3s-Node-IP>:30802/metrics`

### gRPC API

- **集群内访问**: `lemo-service-recommender.lemo-dev.svc.cluster.local:50051`
- **服务发现**: `discovery:///lemo-service-recommender`

## 🛠️ 配置修改

### 修改环境变量

编辑 `k8s-deployment.yaml` 中的 ConfigMap：

```yaml
data:
  config.env: |
    ENV=prod
    LOG_LEVEL=INFO
    MONGODB_URL=mongodb://lemo-mongodb:27017
    # ... 其他配置
```

### 修改副本数

编辑 `k8s-deployment.yaml` 中的 Deployment spec:

```yaml
spec:
  replicas: 2  # 修改副本数
```

### 修改资源限制

编辑 `k8s-deployment.yaml` 中的 resources:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

## 🔄 更新部署

重新运行部署脚本即可：

```bash
./k8s-deploy/deploy-to-k3s.sh
```

脚本会自动构建新镜像并执行滚动更新，服务不会中断。

## ❌ 删除部署

```bash
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete deployment lemo-service-recommender-http
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete deployment lemo-service-recommender-grpc
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete svc lemo-service-recommender-http
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete svc lemo-service-recommender
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete configmap lemo-service-recommender-config
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete sa lemo-service-recommender-sa
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete role lemo-service-recommender-role
kubectl --kubeconfig=k8s-deploy/k3s-jd-config.yaml -n lemo-dev delete rolebinding lemo-service-recommender-rolebinding
```

## 📝 注意事项

1. **首次部署**需要手动创建 `regcred` secret（镜像拉取凭证）
2. **NodePort 端口**（30801, 30802）需确保不与其他服务冲突
3. **资源配置**根据实际负载调整
4. **依赖服务**（MongoDB、Redis、Kafka、Milvus）需提前部署
5. **服务名称** `lemo-service-recommender` 遵循项目统一命名规范

## 🔗 相关链接

- [Kubernetes 文档](https://kubernetes.io/docs/)
- [K3s 文档](https://docs.k3s.io/)
- [阿里云 ACR](https://help.aliyun.com/product/60716.html)

