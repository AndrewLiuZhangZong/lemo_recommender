"""
Flink 作业示例脚本
功能：从 Kafka 消费数据，进行实时处理，写入 Redis/MongoDB
此脚本可以作为 Flink 作业模板的示例使用
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径（如果需要使用项目中的模块）
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from pyflink.datastream import StreamExecutionEnvironment
    from pyflink.datastream.window import TumblingProcessingTimeWindows
    from pyflink.common import Time, WatermarkStrategy
    from pyflink.datastream.functions import ProcessWindowFunction
    from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
    from pyflink.common.serialization import SimpleStringSchema
    PYFLINK_AVAILABLE = True
except ImportError:
    PYFLINK_AVAILABLE = False
    print("⚠️  PyFlink未安装，请确保 Flink Python 环境已配置")


def main():
    """
    主函数 - Flink 作业入口点
    
    此函数会被 Flink 调用作为作业的入口点
    可以通过 args 传递参数，例如：
    --tenant-id tenant1 --scenario-id scenario1 --kafka-topic user-behaviors
    """
    # 解析命令行参数
    args = parse_args()
    
    print(f"🚀 启动 Flink 作业: {args.get('job_name', 'Example Job')}")
    print(f"   参数: {args}")
    
    # 创建 Flink 执行环境
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(args.get('parallelism', 1))
    
    # 配置 Checkpoint（如果启用）
    if args.get('enable_checkpoint', False):
        env.enable_checkpointing(args.get('checkpoint_interval', 60000))
        print(f"   ✓ Checkpoint 已启用，间隔: {args.get('checkpoint_interval', 60000)}ms")
    
    # 配置 Kafka Source
    kafka_source = KafkaSource.builder() \
        .set_bootstrap_servers(args.get('kafka_bootstrap_servers', 'localhost:9092')) \
        .set_topics(args.get('kafka_topic', 'user-behaviors')) \
        .set_group_id(args.get('kafka_group_id', 'flink-job-group')) \
        .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
        .set_value_only_deserializer(SimpleStringSchema()) \
        .build()
    
    # 创建数据流
    data_stream = env.from_source(
        kafka_source,
        WatermarkStrategy.no_watermarks(),
        "Kafka Source"
    )
    
    # 数据处理逻辑
    # 示例：将 JSON 字符串解析并处理
    processed_stream = data_stream \
        .map(lambda x: parse_and_process(x, args)) \
        .filter(lambda x: x is not None)
    
    # 窗口聚合（示例：5分钟滚动窗口）
    class WindowAggregator(ProcessWindowFunction):
        """窗口聚合函数类"""
        def __init__(self, args):
            self.args = args
        
        def process(self, key, context, elements):
            # 将元素转换为列表并聚合
            elements_list = list(elements)
            count = len(elements_list)
            
            result = {
                'key': str(key),
                'window_start': datetime.now().isoformat(),
                'count': count,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"📊 窗口聚合结果 - Key: {key}, Count: {count}")
            
            # ProcessWindowFunction 需要 yield 结果
            yield json.dumps(result)
    
    windowed_stream = processed_stream \
        .key_by(lambda x: x.get('key', 'default')) \
        .window(TumblingProcessingTimeWindows.of(Time.minutes(5))) \
        .process(WindowAggregator(args))
    
    # 输出到 Redis/MongoDB/Kafka（根据配置）
    output_type = args.get('output_type', 'print')  # print, redis, mongodb, kafka
    
    if output_type == 'print':
        # 打印输出（用于测试）
        windowed_stream.print("结果")
    elif output_type == 'redis':
        # TODO: 实现 Redis 输出
        print("⚠️  Redis 输出功能待实现")
        windowed_stream.print("结果")
    elif output_type == 'mongodb':
        # TODO: 实现 MongoDB 输出
        print("⚠️  MongoDB 输出功能待实现")
        windowed_stream.print("结果")
    else:
        windowed_stream.print("结果")
    
    # 执行作业
    print("📊 作业已提交，等待执行...")
    env.execute(args.get('job_name', 'Example Flink Job'))


def parse_args():
    """
    解析命令行参数
    
    返回参数字典
    """
    args = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith('--'):
            key = sys.argv[i][2:]  # 移除 '--'
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                args[key.replace('-', '_')] = sys.argv[i + 1]
                i += 2
            else:
                args[key.replace('-', '_')] = True
                i += 1
        else:
            i += 1
    
    # 设置默认值
    defaults = {
        'job_name': os.getenv('FLINK_JOB_NAME', 'Example Flink Job'),
        'parallelism': int(os.getenv('FLINK_PARALLELISM', '1')),
        'kafka_bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'kafka_topic': os.getenv('KAFKA_TOPIC', 'user-behaviors'),
        'kafka_group_id': os.getenv('KAFKA_GROUP_ID', 'flink-job-group'),
        'enable_checkpoint': os.getenv('FLINK_ENABLE_CHECKPOINT', 'false').lower() == 'true',
        'checkpoint_interval': int(os.getenv('FLINK_CHECKPOINT_INTERVAL', '60000')),
        'output_type': os.getenv('OUTPUT_TYPE', 'print'),
    }
    
    # 合并参数，命令行参数优先级更高
    for key, value in defaults.items():
        if key not in args:
            args[key] = value
    
    return args


def parse_and_process(data_str, args):
    """
    解析并处理单条数据
    
    Args:
        data_str: JSON 字符串
        args: 作业参数
        
    Returns:
        处理后的数据字典，如果解析失败返回 None
    """
    try:
        data = json.loads(data_str)
        
        # 示例处理逻辑：添加时间戳
        data['processed_at'] = datetime.now().isoformat()
        
        # 提取 key 用于分组
        key = f"{data.get('tenant_id', 'default')}_{data.get('scenario_id', 'default')}"
        data['key'] = key
        
        return data
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON 解析失败: {e}, 数据: {data_str[:100]}")
        return None
    except Exception as e:
        print(f"⚠️  数据处理失败: {e}")
        return None


def aggregate_window(key, context, elements, args):
    """
    窗口聚合函数
    
    Args:
        key: 窗口的 key
        context: 窗口上下文
        elements: 窗口内的所有元素（迭代器）
        args: 作业参数
        
    Returns:
        聚合结果（通过 yield 返回）
    """
    # 将迭代器转换为列表
    elements_list = list(elements) if hasattr(elements, '__iter__') else [elements]
    
    # 示例聚合逻辑：统计窗口内的数据数量
    count = len(elements_list)
    
    result = {
        'key': str(key),
        'window_start': datetime.now().isoformat(),
        'count': count,
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"📊 窗口聚合结果 - Key: {key}, Count: {count}")
    
    # 返回结果（ProcessWindowFunction 需要 yield）
    yield json.dumps(result)


if __name__ == '__main__':
    main()

