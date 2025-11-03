"""
简单的 Flink 测试作业
用于验证 PyFlink 环境和 JAR 加载是否正常
不依赖 Kafka
"""
import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common import Types

def main():
    """测试 PyFlink 基础功能"""
    print("=" * 60)
    print("🧪 Flink 简单测试作业")
    print("=" * 60)
    
    # 检查 JAR 文件
    import glob
    jar_files_usrlib = glob.glob("/opt/flink/usrlib/*.jar")
    jar_files_tmp = glob.glob("/tmp/flink-jars/*.jar")
    all_jars = jar_files_usrlib + jar_files_tmp
    
    if all_jars:
        print(f"✓ 发现 {len(all_jars)} 个 JAR 文件:")
        for jar in all_jars:
            print(f"  - {jar}")
    else:
        print("⚠️  未发现任何 JAR 文件")
    
    # 创建执行环境
    print("\n创建 Flink 执行环境...")
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    
    # 注意：不需要显式调用 add_jars()
    # Flink 会自动加载 /opt/flink/usrlib/ 目录的 JAR
    print(f"\n✓ Flink 会自动加载 usrlib 目录的 {len([j for j in all_jars if 'usrlib' in j])} 个 JAR")
    
    # 创建一个简单的数据流
    print("\n创建数据流...")
    data_stream = env.from_collection(
        collection=[
            (1, 'Hello'),
            (2, 'World'),
            (3, 'Flink'),
            (4, 'Test'),
        ],
        type_info=Types.TUPLE([Types.INT(), Types.STRING()])
    )
    
    # 简单的map操作
    result_stream = data_stream.map(
        lambda x: f"ID={x[0]}, Value={x[1]}",
        output_type=Types.STRING()
    )
    
    # 打印结果
    result_stream.print()
    
    # 执行作业
    print("\n执行作业...")
    print("=" * 60)
    env.execute("Simple Test Job")
    
    print("\n✓ 作业执行成功！")
    print("=" * 60)

if __name__ == '__main__':
    main()

