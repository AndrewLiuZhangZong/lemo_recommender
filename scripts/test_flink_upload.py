#!/usr/bin/env python3
"""
测试 Flink JAR/Python 文件上传（使用标准库）
"""
import requests
import sys

FLINK_REST_URL = "http://111.228.39.41:8081"

def test_flink_overview():
    """测试 Flink 服务是否正常"""
    print("\n" + "=" * 60)
    print("检查 Flink 服务状态")
    print("=" * 60)
    
    try:
        response = requests.get(f"{FLINK_REST_URL}/overview", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Flink 服务正常")
            print(f"  版本: {result.get('flink-version', 'unknown')}")
            print(f"  TaskManagers: {result.get('taskmanagers', 0)}")
            print(f"  Slots 总数: {result.get('slots-total', 0)}")
            print(f"  Slots 可用: {result.get('slots-available', 0)}")
            return True
        else:
            print(f"❌ Flink 服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接 Flink 服务: {e}")
        return False

def test_upload_python_script():
    """测试上传 Python 脚本"""
    print("\n" + "=" * 60)
    print("测试上传 Python 脚本到 Flink")
    print("=" * 60)
    
    # 创建一个简单的测试脚本
    test_script = """
from pyflink.datastream import StreamExecutionEnvironment

def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    
    # 简单的数据流处理
    data_stream = env.from_collection([1, 2, 3, 4, 5])
    data_stream.map(lambda x: x * 2).print()
    
    env.execute("Test Python Job")

if __name__ == '__main__':
    main()
"""
    
    print(f"\n✓ 准备测试脚本")
    print(f"  脚本大小: {len(test_script)} 字节")
    
    upload_url = f"{FLINK_REST_URL}/jars/upload"
    print(f"\n上传 URL: {upload_url}")
    
    # 方法1: jarfile + application/x-java-archive（当前 job_manager.py 使用的方法）
    print("\n" + "-" * 60)
    print("方法1: jarfile + application/x-java-archive")
    print("-" * 60)
    try:
        files = {
            'jarfile': ('test_flink_job.py', test_script.encode(), 'application/x-java-archive')
        }
        response = requests.post(upload_url, files=files, timeout=30)
        print(f"  状态码: {response.status_code}")
        print(f"  响应头: {dict(response.headers)}")
        print(f"  响应内容: {response.text[:500]}")
        
        if response.status_code == 200:
            print("\n✅ 方法1 成功!")
            return True, "jarfile + application/x-java-archive"
    except Exception as e:
        print(f"\n❌ 方法1 失败: {e}")
    
    # 方法2: file + text/x-python
    print("\n" + "-" * 60)
    print("方法2: file + text/x-python")
    print("-" * 60)
    try:
        files = {
            'file': ('test_flink_job.py', test_script.encode(), 'text/x-python')
        }
        response = requests.post(upload_url, files=files, timeout=30)
        print(f"  状态码: {response.status_code}")
        print(f"  响应头: {dict(response.headers)}")
        print(f"  响应内容: {response.text[:500]}")
        
        if response.status_code == 200:
            print("\n✅ 方法2 成功!")
            return True, "file + text/x-python"
    except Exception as e:
        print(f"\n❌ 方法2 失败: {e}")
    
    # 方法3: jarfile + application/octet-stream
    print("\n" + "-" * 60)
    print("方法3: jarfile + application/octet-stream")
    print("-" * 60)
    try:
        files = {
            'jarfile': ('test_flink_job.py', test_script.encode(), 'application/octet-stream')
        }
        response = requests.post(upload_url, files=files, timeout=30)
        print(f"  状态码: {response.status_code}")
        print(f"  响应头: {dict(response.headers)}")
        print(f"  响应内容: {response.text[:500]}")
        
        if response.status_code == 200:
            print("\n✅ 方法3 成功!")
            return True, "jarfile + application/octet-stream"
    except Exception as e:
        print(f"\n❌ 方法3 失败: {e}")
    
    # 方法4: 测试上传一个真实的 JAR 文件（如果 Python 不支持）
    print("\n" + "-" * 60)
    print("方法4: 测试上传 JAR 文件（验证端点是否工作）")
    print("-" * 60)
    # 创建一个最小的 ZIP/JAR 文件
    import zipfile
    import io
    
    jar_buffer = io.BytesIO()
    with zipfile.ZipFile(jar_buffer, 'w') as jar:
        jar.writestr('META-INF/MANIFEST.MF', 'Manifest-Version: 1.0\n')
    jar_content = jar_buffer.getvalue()
    
    try:
        files = {
            'jarfile': ('test.jar', jar_content, 'application/x-java-archive')
        }
        response = requests.post(upload_url, files=files, timeout=30)
        print(f"  状态码: {response.status_code}")
        print(f"  响应头: {dict(response.headers)}")
        print(f"  响应内容: {response.text[:500]}")
        
        if response.status_code == 200:
            print("\n✅ 方法4 成功 (JAR 文件可以上传)!")
            print("⚠️  这说明 /jars/upload 端点只接受 JAR 文件，不接受 Python 文件")
            return False, None
    except Exception as e:
        print(f"\n❌ 方法4 失败: {e}")
    
    return False, None

def main():
    print("\n🚀 Flink 文件上传测试工具\n")
    
    # 1. 检查 Flink 服务
    if not test_flink_overview():
        print("\n❌ Flink 服务不可用，终止测试")
        sys.exit(1)
    
    # 2. 测试上传
    success, method = test_upload_python_script()
    
    print("\n" + "=" * 60)
    if success:
        print(f"✅ 测试成功！有效的上传方法: {method}")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ 所有上传方法都失败了")
        print("=" * 60)
        print("\n💡 可能的原因:")
        print("  1. Flink /jars/upload 端点只接受 JAR 文件")
        print("  2. Python 作业需要通过其他方式提交:")
        print("     - 使用 K8s Job + flink run")
        print("     - 使用 Flink Python Client 直接提交")
        print("     - 将 Python 脚本打包成 PyFlink JAR")
        print("\n📚 参考文档:")
        print("  https://nightlies.apache.org/flink/flink-docs-release-1.19/docs/deployment/cli/#submitting-pyflink-jobs")
        sys.exit(1)

if __name__ == '__main__':
    main()
