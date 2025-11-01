# Flink 作业模板配置说明

## 作业类型和配置格式

### 1. PYTHON_SCRIPT（Python 脚本）

**配置格式：**
```json
{
  "script_path": "/path/to/script.py",
  "entry_point": "main",
  "args": ["arg1", "arg2"]
}
```

**字段说明：**
- `script_path` (必填): Python 脚本文件的路径
  - 可以是绝对路径，如：`/opt/flink/jobs/my_job.py`
  - 也可以是相对路径（相对于 Flink 作业目录），如：`jobs/my_job.py`
  - 示例：`"/opt/flink/jobs/item_hot_score_calculator.py"`
  
- `entry_point` (必填): 脚本中的入口函数名
  - 通常是 `main`，也可以是其他函数名
  - 脚本中需要有对应的函数定义，如：`def main():`
  - 示例：`"main"`

- `args` (可选): 传递给脚本的命令行参数列表
  - 示例：`["--tenant-id", "tenant1", "--scenario-id", "scenario1"]`

**示例：**
```json
{
  "script_path": "/opt/flink/jobs/item_hot_score_calculator.py",
  "entry_point": "main",
  "args": ["--tenant-id", "tenant1"]
}
```

### 2. JAR（Flink JAR）

**配置格式：**
```json
{
  "jar_path": "/path/to/job.jar",
  "main_class": "com.example.MainClass",
  "args": ["arg1", "arg2"]
}
```

**字段说明：**
- `jar_path` (必填): JAR 文件的路径
- `main_class` (必填): 主类的完整类名
- `args` (可选): 传递给主类的参数

**示例：**
```json
{
  "jar_path": "/opt/flink/lib/my-job.jar",
  "main_class": "com.example.recommendation.JobMain",
  "args": ["--config", "/etc/flink/config.json"]
}
```

### 3. SQL（Flink SQL）

**配置格式：**
```json
{
  "sql": "CREATE TABLE ...",
  "sql_file": "/path/to/query.sql"
}
```

**字段说明：**
- `sql` (可选): SQL 语句字符串（直接在配置中写 SQL）
- `sql_file` (可选): SQL 文件路径（如果 SQL 很长，可以放在文件中）

**注意：** `sql` 和 `sql_file` 至少需要提供一个

**示例：**
```json
{
  "sql": "CREATE TABLE orders (...); INSERT INTO orders SELECT * FROM kafka_source;"
}
```

或

```json
{
  "sql_file": "/opt/flink/sql/orders_etl.sql"
}
```

### 4. PYTHON_FLINK（PyFlink）

**配置格式：**
```json
{
  "script_path": "/path/to/pyflink_job.py",
  "python_env": "/path/to/venv",
  "entry_point": "main"
}
```

**字段说明：**
- `script_path` (必填): PyFlink 脚本文件路径
- `python_env` (可选): Python 虚拟环境路径
- `entry_point` (必填): 入口函数名

**示例：**
```json
{
  "script_path": "/opt/flink/pyflink/realtime_processor.py",
  "python_env": "/opt/flink/venv",
  "entry_point": "main"
}
```

## 通用字段

所有作业类型都支持以下通用配置字段：

- `parallelism`: 并行度（在模板级别设置，也可以在提交作业时覆盖）
- `checkpoints_enabled`: 是否启用 Checkpoint
- `checkpoint_interval_ms`: Checkpoint 间隔（毫秒）
- `task_manager_memory`: TaskManager 内存
- `job_manager_memory`: JobManager 内存

## 注意事项

1. **路径格式**：使用绝对路径更可靠，避免相对路径导致的找不到文件问题
2. **入口函数**：确保脚本中定义了对应的入口函数
3. **参数传递**：通过 `args` 字段传递参数，在脚本中可以通过 `sys.argv` 获取
4. **依赖管理**：确保脚本所需的 Python 包都已安装到 Flink 环境中

