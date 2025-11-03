"""
最小化 PyFlink 测试脚本
完全遵循 Apache Flink 官方最佳实践
不做任何额外的 JAR 加载操作
"""
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common import Types

def main():
    """
    最简单的 Flink 作业
    遵循 Apache Flink 官方文档标准
    """
    print("=" * 60)
    print("Flink Minimal Test Job")
    print("=" * 60)
    
    # 1. 创建执行环境（标准方式）
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    print("✓ Execution environment created")
    
    # 2. 创建简单数据流（标准方式）
    data_stream = env.from_collection(
        collection=[1, 2, 3, 4, 5],
        type_info=Types.INT()
    )
    print("✓ Data stream created")
    
    # 3. 简单转换（标准方式）
    result = data_stream.map(lambda x: x * 2, output_type=Types.INT())
    print("✓ Transformation applied")
    
    # 4. 输出（标准方式）
    result.print()
    print("✓ Sink configured")
    
    # 5. 执行作业（标准方式）
    print("✓ Executing job...")
    print("=" * 60)
    env.execute("Minimal Test Job")
    print("✓ Job completed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    main()

