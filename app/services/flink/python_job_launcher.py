"""
Flink Python 作业启动器

通过生成一个临时的 PyFlink 脚本，该脚本负责：
1. 从远程 URL 下载用户的 Python 脚本
2. 下载所需的 JAR 依赖
3. 执行用户脚本

这个启动器脚本会被上传到 Flink 并执行。
"""
import tempfile
import os
from typing import List, Dict, Any


def generate_python_launcher_script(
    script_url: str,
    jar_dependencies: List[str],
    job_args: Dict[str, Any],
    parallelism: int = 1
) -> str:
    """
    生成 Python 启动器脚本
    
    Args:
        script_url: 用户 Python 脚本的远程 URL
        jar_dependencies: JAR 依赖列表（URL 或路径）
        job_args: 传递给用户脚本的参数
        parallelism: 并行度
        
    Returns:
        启动器脚本内容
    """
    # 构建参数字符串
    args_str = " ".join([f"--{k} {v}" for k, v in job_args.items()])
    
    # 构建 JAR 下载和导入逻辑
    jar_imports = []
    jar_download_code = ""
    
    for i, jar_url in enumerate(jar_dependencies):
        jar_name = f"dep_{i}.jar"
        if jar_url.startswith("http://") or jar_url.startswith("https://"):
            jar_download_code += f"""
# 下载 JAR 依赖 {i+1}
import urllib.request
jar_path_{i} = '/tmp/{jar_name}'
urllib.request.urlretrieve('{jar_url}', jar_path_{i})
print(f'✓ 下载 JAR 依赖: {jar_name}')
"""
            jar_imports.append(f"jar_path_{i}")
    
    # 生成启动器脚本
    launcher_script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flink Python 作业启动器
自动下载并执行用户脚本
"""
import sys
import os
import urllib.request
import tempfile

print("=" * 60)
print("Flink Python Job Launcher")
print("=" * 60)

# 设置环境变量
os.environ['PYFLINK_CLIENT_EXECUTABLE'] = 'python3'
os.environ['PYFLINK_EXECUTABLE'] = 'python3'

# 下载用户脚本
script_url = '{script_url}'
script_name = script_url.split('/')[-1]
script_path = f'/tmp/{{script_name}}'

print(f'📥 下载用户脚本: {{script_url}}')
urllib.request.urlretrieve(script_url, script_path)
print(f'✓ 脚本已下载到: {{script_path}}')

{jar_download_code}

# 添加 JAR 到 classpath（如果有）
jar_paths = [{', '.join(f"'{jp}'" for jp in jar_imports)}]
if jar_paths:
    print(f'📦 加载 {{len(jar_paths)}} 个 JAR 依赖')
    # 通过环境变量传递给 PyFlink
    os.environ['FLINK_CONF_DIR'] = '/opt/flink/conf'

# 执行用户脚本
print(f'🚀 执行用户脚本: {{script_name}}')
print("=" * 60)

# 导入用户脚本为模块
import importlib.util
spec = importlib.util.spec_from_file_location("user_script", script_path)
user_module = importlib.util.module_from_spec(spec)
sys.modules["user_script"] = user_module

# 执行用户脚本
try:
    spec.loader.exec_module(user_module)
    
    # 调用 main 函数（如果存在）
    if hasattr(user_module, 'main'):
        print("✓ 调用 main() 函数")
        user_module.main()
    else:
        print("⚠️  脚本没有 main() 函数，已执行模块级代码")
        
    print("=" * 60)
    print("✓ 作业执行完成")
    print("=" * 60)
except Exception as e:
    print("=" * 60)
    print(f"✗ 作业执行失败: {{e}}")
    print("=" * 60)
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
    
    return launcher_script


async def create_launcher_script_file(
    script_url: str,
    jar_dependencies: List[str],
    job_args: Dict[str, Any],
    parallelism: int = 1
) -> str:
    """
    创建启动器脚本临时文件
    
    Returns:
        临时文件路径
    """
    launcher_content = generate_python_launcher_script(
        script_url=script_url,
        jar_dependencies=jar_dependencies,
        job_args=job_args,
        parallelism=parallelism
    )
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        prefix='flink_launcher_',
        delete=False
    ) as f:
        f.write(launcher_content)
        return f.name

