#!/bin/bash

# Flink 作业调试脚本
# 用于查看 K8s Job 的详细日志和 Flink 命令

# 使用指定的 kubeconfig
export KUBECONFIG="$(dirname "$0")/../k8s-deploy/k3s-jd-config.yaml"

echo "=========================================="
echo "Flink Python Job 调试信息"
echo "=========================================="
echo "使用 kubeconfig: $KUBECONFIG"
echo ""

# 1. 查看最近的 Flink Python Job
echo "1. 最近的 Flink Python Job:"
kubectl get jobs -n lemo-dev -l app=flink-python-job --sort-by=.metadata.creationTimestamp | tail -10
echo ""

# 2. 查看最新 Job 的详细信息
LATEST_JOB=$(kubectl get jobs -n lemo-dev -l app=flink-python-job --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}' 2>/dev/null)

if [ -z "$LATEST_JOB" ]; then
    echo "错误: 没有找到 Flink Python Job"
    exit 1
fi

echo "2. 最新 Job 名称: $LATEST_JOB"
echo ""

# 3. 查看 Job 的 Pod
echo "3. Job 对应的 Pod:"
kubectl get pods -n lemo-dev -l job-name=$LATEST_JOB
echo ""

# 4. 获取 Pod 名称
POD_NAME=$(kubectl get pods -n lemo-dev -l job-name=$LATEST_JOB -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POD_NAME" ]; then
    echo "错误: 没有找到对应的 Pod"
    exit 1
fi

echo "4. Pod 名称: $POD_NAME"
echo ""

# 5. 查看 Pod 状态
echo "5. Pod 状态详情:"
kubectl describe pod -n lemo-dev $POD_NAME | grep -A 10 "State:"
echo ""

# 6. 查看 Pod 的完整日志
echo "6. Pod 完整日志:"
echo "=========================================="
kubectl logs -n lemo-dev $POD_NAME
echo "=========================================="
echo ""

# 7. 查看 Job 的环境变量配置
echo "7. Job 的环境变量:"
kubectl get job -n lemo-dev $LATEST_JOB -o jsonpath='{.spec.template.spec.containers[0].env}' | jq .
echo ""

# 8. 查看实际执行的命令
echo "8. 实际执行的命令:"
kubectl get job -n lemo-dev $LATEST_JOB -o jsonpath='{.spec.template.spec.containers[0].args}' | jq .
echo ""

# 9. 测试 Flink 镜像
echo "9. 测试 Flink 镜像是否支持 Python:"
echo "创建测试 Pod..."
kubectl run flink-test -n lemo-dev --image=registry.cn-beijing.aliyuncs.com/lemo_zls/flink-python:latest --restart=Never --rm -i --command -- /opt/flink/bin/flink --version
echo ""

# 10. 检查 Flink 集群连接
echo "10. 检查 Flink 集群连接:"
FLINK_HOST=$(kubectl get configmap -n lemo-dev lemo-service-recommender-config -o jsonpath='{.data.FLINK_JOBMANAGER_RPC_ADDRESS}' | cut -d: -f1)
FLINK_PORT=$(kubectl get configmap -n lemo-dev lemo-service-recommender-config -o jsonpath='{.data.FLINK_JOBMANAGER_RPC_ADDRESS}' | cut -d: -f2)
echo "Flink JobManager: $FLINK_HOST:$FLINK_PORT"
nc -zv $FLINK_HOST $FLINK_PORT 2>&1 || echo "无法连接到 Flink JobManager RPC 端口"
echo ""

echo "=========================================="
echo "调试完成"
echo "=========================================="

