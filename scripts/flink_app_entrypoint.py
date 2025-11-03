#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flink Application Mode 入口点

功能：
1. 从环境变量读取用户脚本 URL
2. 下载用户脚本到本地
3. 下载 JAR 依赖（如果有）
4. 执行用户脚本

环境变量：
- SCRIPT_URL: 用户 Python 脚本的 URL（必需）
- JAR_URLS: JAR 依赖 URL 列表，逗号分隔（可选）
- KAFKA_SERVERS: Kafka 服务器地址（可选，传递给用户脚本）
- CHECKPOINT_INTERVAL: Checkpoint 间隔（可选）
- 其他自定义环境变量...

使用示例：
  export SCRIPT_URL=https://file.lemo-ai.com/scripts/example.py
  export JAR_URLS=https://repo1.maven.org/maven2/.../kafka-connector.jar
  python3 entrypoint.py
"""

import os
import sys
import urllib.request
import traceback
from pathlib import Path


def log(message: str, level: str = "INFO"):
    """
    打印日志
    """
    print(f"[{level}] {message}", flush=True)


def download_file(url: str, dest_path: str) -> bool:
    """
    下载文件
    
    Args:
        url: 文件 URL
        dest_path: 目标路径
        
    Returns:
        是否成功
    """
    try:
        log(f"下载文件: {url} -> {dest_path}")
        urllib.request.urlretrieve(url, dest_path)
        file_size = os.path.getsize(dest_path)
        log(f"✓ 下载完成，文件大小: {file_size} bytes")
        return True
    except Exception as e:
        log(f"✗ 下载失败: {e}", "ERROR")
        traceback.print_exc()
        return False


def download_script() -> str:
    """
    下载用户 Python 脚本
    
    Returns:
        脚本本地路径
    """
    script_url = os.environ.get('SCRIPT_URL')
    if not script_url:
        raise ValueError("环境变量 SCRIPT_URL 未设置")
    
    # 提取文件名
    script_filename = script_url.split('/')[-1]
    if not script_filename.endswith('.py'):
        script_filename += '.py'
    
    script_path = f"/tmp/flink-scripts/{script_filename}"
    
    # 确保目录存在
    os.makedirs("/tmp/flink-scripts", exist_ok=True)
    
    # 下载脚本
    if not download_file(script_url, script_path):
        raise RuntimeError(f"脚本下载失败: {script_url}")
    
    return script_path


def download_jars():
    """
    下载 JAR 依赖并复制到 Flink lib 目录
    
    Returns:
        JAR 文件路径列表
    """
    jar_urls_str = os.environ.get('JAR_URLS', '')
    if not jar_urls_str:
        log("无 JAR 依赖需要下载")
        return []
    
    jar_urls = [url.strip() for url in jar_urls_str.split(',') if url.strip()]
    if not jar_urls:
        return []
    
    log(f"需要下载 {len(jar_urls)} 个 JAR 依赖")
    
    # 确保临时目录和 Flink usrlib 目录存在
    os.makedirs("/tmp/flink-jars", exist_ok=True)
    os.makedirs("/opt/flink/usrlib", exist_ok=True)
    
    jar_paths = []
    for i, jar_url in enumerate(jar_urls, 1):
        jar_filename = jar_url.split('/')[-1]
        if not jar_filename.endswith('.jar'):
            jar_filename += '.jar'
        
        temp_jar_path = f"/tmp/flink-jars/{jar_filename}"
        
        log(f"[{i}/{len(jar_urls)}] 下载 JAR: {jar_filename}")
        if download_file(jar_url, temp_jar_path):
            # 复制到 Flink usrlib 目录（PyFlink 会自动加载这个目录的 JAR）
            usrlib_jar_path = f"/opt/flink/usrlib/{jar_filename}"
            try:
                import shutil
                shutil.copy2(temp_jar_path, usrlib_jar_path)
                log(f"✓ JAR 已复制到: {usrlib_jar_path}")
                jar_paths.append(usrlib_jar_path)
            except Exception as e:
                log(f"⚠️  复制 JAR 失败: {e}，使用临时路径", "WARN")
                jar_paths.append(temp_jar_path)
        else:
            log(f"⚠️  JAR 下载失败，继续执行: {jar_url}", "WARN")
    
    log(f"✓ 成功下载 {len(jar_paths)} 个 JAR 文件")
    return jar_paths


def execute_script(script_path: str):
    """
    执行用户脚本
    
    Args:
        script_path: 脚本路径
    """
    log(f"执行用户脚本: {script_path}")
    log("=" * 60)
    
    try:
        # 将脚本目录添加到 sys.path，使脚本可以导入同目录的模块
        script_dir = os.path.dirname(os.path.abspath(script_path))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        
        # 使用 exec() 直接执行脚本，这样可以正确触发 if __name__ == '__main__':
        # 创建一个全局命名空间，设置 __name__ = '__main__'
        global_namespace = {
            '__name__': '__main__',
            '__file__': script_path,
            '__builtins__': __builtins__,
        }
        
        # 读取并执行脚本
        with open(script_path, 'r', encoding='utf-8') as f:
            script_code = f.read()
        
        # 执行脚本
        exec(script_code, global_namespace)
        
        log("=" * 60)
        log("✓ 用户脚本执行完成", "SUCCESS")
        
    except Exception as e:
        log("=" * 60)
        log(f"✗ 用户脚本执行失败: {e}", "ERROR")
        traceback.print_exc()
        sys.exit(1)


def main():
    """
    主函数
    """
    log("=" * 60)
    log("Flink Application Mode Entrypoint")
    log("=" * 60)
    log("")
    
    # 打印环境信息
    log(f"Python 版本: {sys.version}")
    log(f"工作目录: {os.getcwd()}")
    log(f"FLINK_HOME: {os.environ.get('FLINK_HOME', 'N/A')}")
    log("")
    
    # 打印关键环境变量
    log("关键环境变量:")
    for key in ['SCRIPT_URL', 'JAR_URLS', 'KAFKA_SERVERS', 'CHECKPOINT_INTERVAL']:
        value = os.environ.get(key, 'N/A')
        log(f"  {key} = {value}")
    log("")
    
    try:
        # 1. 下载 JAR 依赖
        log("步骤 1/3: 下载 JAR 依赖...")
        jar_paths = download_jars()
        log("")
        
        # 2. 下载用户脚本
        log("步骤 2/3: 下载用户脚本...")
        script_path = download_script()
        log("")
        
        # 3. 执行用户脚本
        log("步骤 3/3: 执行用户脚本...")
        execute_script(script_path)
        
        log("")
        log("=" * 60)
        log("✓ Flink Application 执行成功", "SUCCESS")
        log("=" * 60)
        
    except Exception as e:
        log("=" * 60)
        log(f"✗ Flink Application 执行失败: {e}", "ERROR")
        log("=" * 60)
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

