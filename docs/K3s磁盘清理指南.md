# K3s 磁盘清理指南

## 问题背景

在生产环境中，K3s 的容器镜像、日志文件会不断累积，导致磁盘空间不足。特别是频繁部署时，会产生大量旧版本镜像。

## 常见问题

### 1. containerd 超时
```
rpc error: code = DeadlineExceeded desc = context deadline exceeded
```
**原因**：磁盘 I/O 负载过高，containerd 响应缓慢  
**解决**：重启 k3s 服务

### 2. ImagePullBackOff
**原因**：磁盘空间不足，无法拉取新镜像  
**解决**：清理旧镜像和日志

---

## ⚠️ 紧急清理脚本（安全版）

**❌ 警告：之前版本的脚本有严重问题，会导致整个集群崩溃！已修复。**

### 安全清理脚本

保存为 `safe-cleanup.sh`：

```bash
#!/bin/bash
set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧹 K3s 磁盘空间安全清理"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查初始空间
echo "📊 清理前磁盘空间："
df -h | grep -E "Filesystem|/$"
echo ""

# 1. 清理未使用的镜像（使用 crictl，不直接删除 blob）
echo "[1/5] 清理未使用的容器镜像..."
k3s crictl rmi --prune 2>/dev/null || echo "  镜像清理失败，跳过..."

# 2. 清理日志文件
echo "[2/5] 清理日志文件..."
find /var/log/pods -name "*.log" -type f -size +100M -exec truncate -s 50M {} \; 2>/dev/null || true
journalctl --vacuum-size=500M
find /var/log -name "*.log.*" -type f -delete 2>/dev/null || true

# 3. 清理失败的 Pod
echo "[3/5] 清理失败的 Pod..."
kubectl delete pods --all-namespaces --field-selector=status.phase=Failed 2>/dev/null || true
kubectl delete pods --all-namespaces --field-selector=status.phase=Unknown 2>/dev/null || true

# 4. 清理临时文件
echo "[4/5] 清理临时文件..."
rm -rf /tmp/* 2>/dev/null || true
rm -rf /var/tmp/* 2>/dev/null || true

# 5. 清理系统缓存
echo "[5/5] 清理系统缓存..."
yum clean all 2>/dev/null || true

# 检查结果
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 清理完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 清理后磁盘空间："
df -h | grep -E "Filesystem|/$"
echo ""
echo "🔍 K3s 状态："
systemctl status k3s --no-pager | head -5
```

### 使用方法

```bash
# 在服务器上执行
chmod +x safe-cleanup.sh
sudo ./safe-cleanup.sh
```

**⚠️ 重要说明：**
- ✅ 使用 `k3s crictl rmi --prune` 安全清理未使用的镜像
- ❌ **绝不直接删除** `/var/lib/rancher/k3s/agent/containerd/` 下的 blob 文件
- ❌ **绝不直接删除** snapshots 目录
- ✅ 让 containerd 自己管理镜像存储

---

## 分步清理命令

如果需要手动清理，可以按以下步骤执行：

### 1️⃣ 检查磁盘使用情况

```bash
# 查看磁盘空间
df -h

# 查看目录占用
du -sh /var/lib/rancher/* | sort -rh
du -sh /var/log/* | sort -rh

# 查看 containerd 存储
du -sh /var/lib/rancher/k3s/agent/containerd/*
```

### 2️⃣ 清理容器镜像

```bash
# 查看所有镜像
k3s crictl images

# 查看推荐服务镜像（重点）
k3s crictl images | grep lemo-service-recommender

# 清理未使用的镜像（如果 containerd 正常）
k3s crictl rmi --prune

# 手动删除指定镜像
k3s crictl rmi <IMAGE_ID>
```

### 3️⃣ 清理失败的 Pod

```bash
# 删除失败的 Pod
kubectl delete pods -n lemo-dev --field-selector=status.phase=Failed

# 删除 ImagePullBackOff 的旧 Pod
kubectl delete pods -n lemo-dev -l app=lemo-service-recommender --field-selector=status.phase!=Running

# 清理已停止的容器
k3s crictl ps -a | grep -E 'Exited|Error' | awk '{print $1}' | xargs -r k3s crictl rm
```

### 4️⃣ 清理日志文件

```bash
# 清理大日志文件（>100MB）
find /var/log/pods -name "*.log" -type f -size +100M -delete

# 清空所有 Pod 日志（保留文件但清空内容）
find /var/log/pods -name "*.log" -type f -exec truncate -s 0 {} \;

# 清理 journal 日志（只保留最近 7 天）
journalctl --vacuum-time=7d

# 或限制总大小为 200MB
journalctl --vacuum-size=200M

# 清理旧的压缩日志
find /var/log -name "*.log.*.gz" -delete
find /var/log -name "*.log.[0-9]*" -delete
```

### 5️⃣ 清理临时文件

```bash
# 清理临时目录
rm -rf /tmp/*
rm -rf /var/tmp/*

# 清理 YUM 缓存
yum clean all
```

### 6️⃣ 重启 K3s

```bash
# 重启 k3s 服务
systemctl restart k3s

# 查看状态
systemctl status k3s

# 查看日志
journalctl -u k3s -f
```

---

## ❌ 危险操作警告

**以下操作已被证实会导致集群崩溃，切勿使用：**

```bash
# ❌ 绝不执行以下命令！
rm -rf /var/lib/rancher/k3s/agent/containerd/io.containerd.content.v1.content/blobs/*
rm -rf /var/lib/rancher/k3s/agent/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/*
rm -rf /var/lib/rancher/k3s/agent/containerd/*
```

**后果：**
- 删除所有镜像的 blob 数据，包括系统镜像（pause、coredns 等）
- 导致所有 Pod 无法启动
- 需要完全重建 containerd 才能恢复

---

## 集群崩溃后的修复方法

如果不小心执行了危险操作导致集群崩溃，执行以下修复：

```bash
#!/bin/bash
# K3s Containerd 完全修复脚本

echo "🔧 修复 K3s Containerd..."

# 停止 k3s
systemctl stop k3s
sleep 5

# 清理损坏的 containerd 数据
rm -rf /var/lib/rancher/k3s/agent/containerd/io.containerd.content.v1.content/*
rm -rf /var/lib/rancher/k3s/agent/containerd/io.containerd.metadata.v1.bolt/*
rm -rf /var/lib/rancher/k3s/agent/containerd/io.containerd.snapshotter.v1.overlayfs/*

# 清理旧的 Pod 数据
rm -rf /var/lib/rancher/k3s/agent/pod-manifests/*
rm -rf /var/log/pods/*
rm -rf /var/lib/kubelet/pods/*

# 启动 k3s（会重新拉取所有系统镜像）
systemctl start k3s

echo "等待 k3s 启动（约 3 分钟）..."
sleep 180

# 检查状态
kubectl get nodes
kubectl get pods -A
```

---

## 预防措施

### 1. 自动清理策略

创建定时清理任务 `/etc/cron.daily/k3s-cleanup`：

```bash
#!/bin/bash
# K3s 每日自动清理

# 清理未使用的镜像
k3s crictl rmi --prune

# 清理大日志文件
find /var/log/pods -name "*.log" -type f -size +100M -exec truncate -s 50M {} \;

# 清理 journal 日志
journalctl --vacuum-size=500M

# 记录清理结果
echo "$(date): K3s 清理完成" >> /var/log/k3s-cleanup.log
df -h / >> /var/log/k3s-cleanup.log
```

设置权限：
```bash
chmod +x /etc/cron.daily/k3s-cleanup
```

### 2. 部署策略优化

修改 `k8s-deploy/deploy-http-grpc-service.sh`（或其他部署脚本），每次部署时清理旧镜像：

```bash
# 在推送新镜像后添加
echo "清理服务器上的旧版本镜像..."
kubectl --kubeconfig=$KUBECONFIG_FILE exec -n $NAMESPACE deployment/lemo-service-recommender-http -- \
  sh -c "crictl images | grep lemo-service-recommender | awk '{print \$3}' | tail -n +3 | xargs -r crictl rmi" || true
```

### 3. 监控告警

设置磁盘空间告警阈值：

```bash
# 检查磁盘使用率
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

if [ $DISK_USAGE -gt 80 ]; then
    echo "警告：磁盘使用率已达 ${DISK_USAGE}%"
    # 发送告警（集成钉钉/企业微信）
fi
```

---

## 常见问题排查

### Q1: 清理后服务无法启动？

```bash
# 检查 k3s 状态
systemctl status k3s
journalctl -u k3s -n 50

# 检查节点状态
kubectl get nodes

# 检查 Pod 状态
kubectl get pods -A
```

### Q2: 镜像拉取失败？

```bash
# 检查镜像仓库凭证
kubectl get secrets -n lemo-dev | grep regcred

# 重新创建 secret
kubectl delete secret regcred -n lemo-dev
kubectl create secret docker-registry regcred \
  --docker-server=registry.cn-beijing.aliyuncs.com \
  --docker-username=<用户名> \
  --docker-password=<密码> \
  -n lemo-dev
```

### Q3: containerd 仍然超时？

```bash
# 检查 containerd 进程
ps aux | grep containerd

# 查看 containerd 日志
journalctl -u k3s -f | grep containerd

# 重启整个服务器（最后手段）
reboot
```

---

## 参考资料

- [K3s 官方文档](https://docs.k3s.io/)
- [containerd 镜像管理](https://github.com/containerd/containerd/blob/main/docs/ops.md)
- [kubectl 资源清理](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/)

