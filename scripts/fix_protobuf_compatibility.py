#!/usr/bin/env python3
"""
批量修复 gRPC 生成的 Python 文件，禁用 protobuf 版本检查
使其兼容 protobuf 5.x（用于 TensorFlow 2.15 兼容性）
"""

import os
import re
from pathlib import Path


def fix_pb2_file(file_path: Path):
    """修复单个 _pb2.py 文件"""
    print(f"处理: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经修复过
    if '# 禁用版本检查' in content:
        print(f"  ✓ 已修复，跳过")
        return False
    
    # 查找版本检查代码块
    pattern = r'(_runtime_version\.ValidateProtobufRuntimeVersion\([^)]+\))'
    
    if not re.search(pattern, content, re.DOTALL):
        print(f"  ⊘ 无需修复")
        return False
    
    # 替换版本检查代码
    replacement = (
        '# 禁用版本检查以兼容 protobuf 5.x（用于 TensorFlow 兼容性）\n'
        '# \\1'
    )
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  ✅ 已修复")
    return True


def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔧 批量修复 Protobuf 版本兼容性")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    # 查找所有 _pb2.py 文件
    grpc_dir = Path(__file__).parent.parent / 'app' / 'grpc_generated'
    pb2_files = list(grpc_dir.rglob('*_pb2.py'))
    
    if not pb2_files:
        print("❌ 未找到 _pb2.py 文件")
        return 1
    
    print(f"📋 找到 {len(pb2_files)} 个文件")
    print()
    
    fixed_count = 0
    for pb2_file in pb2_files:
        if fix_pb2_file(pb2_file):
            fixed_count += 1
    
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ 完成！共修复 {fixed_count}/{len(pb2_files)} 个文件")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return 0


if __name__ == '__main__':
    exit(main())

