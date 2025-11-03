# Flink Python 作业依赖配置指南

## 问题

提交 Python 作业时报错：
```
TypeError: Could not found the Java class 'org.apache.flink.connector.kafka.source.KafkaSource.builder'. 
The Java dependencies could be specified via command line argument '--jarfile' or the config option 'pipeline.jars'
```

## 原因

PyFlink 底层依赖 Java connector JAR 包。使用 Kafka、JDBC、Elasticsearch 等 connector 时，需要在提交作业时指定对应的 JAR 文件。

---

## 解决方案1: 在作业模板中配置 JAR 依赖（推荐）

### 1. 查看 Flink 镜像中可用的 connector

```bash
# 进入 Flink 容器
docker exec -it lemo-flink ls -lh /opt/flink/opt/

# 常见的 connector:
# flink-connector-kafka-xxx.jar
# flink-connector-jdbc-xxx.jar
# flink-connector-elasticsearch-xxx.jar
# flink-sql-connector-kafka-xxx.jar
```

### 2. 在作业模板的 `config` 中添加 `jar_files`

```json
{
  "script_path": "https://file.lemo-ai.com/xxx.py",
  "entry_point": "main",
  "args": [],
  "jar_files": [
    "/opt/flink/opt/flink-sql-connector-kafka-3.1.0-1.19.jar"
  ]
}
```

### 3. 前端创建模板时的示例

在创建作业模板时，在 **高级配置** 中添加：

```javascript
{
  "script_path": "https://file.lemo-ai.com/your_script.py",
  "jar_files": [
    "/opt/flink/opt/flink-sql-connector-kafka-3.1.0-1.19.jar"
  ]
}
```

---

## 解决方案2: 预先将 JAR 复制到 lib 目录

修改 `Dockerfile.flink-python`，将常用 connector 复制到 `/opt/flink/lib/`：

```dockerfile
# 将 Kafka connector 移动到 lib 目录（自动加载）
RUN cp /opt/flink/opt/flink-sql-connector-kafka-*.jar /opt/flink/lib/
```

**优点**: 无需在模板中配置，自动加载  
**缺点**: 所有 connector 都会加载，可能影响性能

---

## 解决方案3: 使用 Flink 配置文件（不推荐）

修改 `flink-conf.yaml`：

```yaml
pipeline.jars: file:///opt/flink/opt/flink-sql-connector-kafka-3.1.0-1.19.jar
```

**缺点**: 需要重启 Flink 集群，不够灵活

---

## 常用 Connector JAR 路径

### Kafka Connector
```
/opt/flink/opt/flink-sql-connector-kafka-3.1.0-1.19.jar
```

用途：读写 Kafka 消息

### JDBC Connector
```
/opt/flink/opt/flink-connector-jdbc-3.2.0-1.19.jar
```

用途：读写 MySQL、PostgreSQL 等数据库

### Elasticsearch Connector
```
/opt/flink/opt/flink-sql-connector-elasticsearch7-3.1.0-1.19.jar
```

用途：写入 Elasticsearch

---

## 提交命令示例

手动提交时的完整命令：

```bash
/opt/flink/bin/flink run \
  -m 111.228.39.41:6123 \
  -p 2 \
  --jarfile /opt/flink/opt/flink-sql-connector-kafka-3.1.0-1.19.jar \
  -py /tmp/your_script.py
```

---

## 当前系统的实现

系统会自动从模板配置中读取 `jar_files`，并添加到 `flink run` 命令中：

```python
# 模板配置
{
  "jar_files": [
    "/opt/flink/opt/flink-sql-connector-kafka-3.1.0-1.19.jar"
  ]
}

# 生成的命令
/opt/flink/bin/flink run -m 111.228.39.41:6123 -p 1 \
  --jarfile /opt/flink/opt/flink-sql-connector-kafka-3.1.0-1.19.jar \
  -py /tmp/script.py
```

---

## 快速修复当前问题

### 步骤1: 查找 Kafka connector JAR

```bash
# SSH 到服务器
ssh root@111.228.39.41

# 查看 Flink 容器中的 JAR
docker exec lemo-flink ls -lh /opt/flink/opt/ | grep kafka
```

### 步骤2: 更新作业模板配置

在 MongoDB 中更新模板配置：

```javascript
db.job_templates.updateOne(
  { "template_id": "your_template_id" },
  {
    $set: {
      "config.jar_files": [
        "/opt/flink/opt/flink-sql-connector-kafka-3.1.0-1.19.jar"
      ]
    }
  }
)
```

### 步骤3: 重新提交作业

使用更新后的模板重新提交作业即可。

---

## 注意事项

1. **JAR 版本匹配**: 确保 connector JAR 版本与 Flink 版本兼容
2. **多个 JAR**: 可以指定多个 JAR 文件
3. **路径必须存在**: JAR 文件路径必须在 K8s Job Pod 中可访问
4. **镜像一致性**: 确保 `flink-python` 镜像包含所需的 JAR 文件

---

## 验证

提交作业后，查看 K8s Job 日志：

```bash
kubectl logs -n lemo-dev -l app=flink-python-job --tail=100
```

应该看到类似输出：
```
开始提交 Flink 作业...
添加 JAR 依赖: ['/opt/flink/opt/flink-sql-connector-kafka-3.1.0-1.19.jar']
Job has been submitted with JobID abc123...
```

