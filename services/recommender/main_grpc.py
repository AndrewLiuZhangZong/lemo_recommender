"""
gRPC 服务启动入口
启动 gRPC 服务
"""
import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.grpc_server.server import serve
from app.core.config import settings


def main():
    """启动 gRPC 服务"""
    # 从环境变量或配置读取 host 和 port
    host = os.getenv("GRPC_HOST", getattr(settings, 'grpc_host', '0.0.0.0'))
    port = int(os.getenv("GRPC_PORT", getattr(settings, 'grpc_port', 50051)))
    
    print("=" * 70)
    print("🚀 启动 gRPC 服务...")
    print("=" * 70)
    print(f"   gRPC 地址: {host}:{port}")
    print("=" * 70)
    
    asyncio.run(serve(host=host, port=port))


if __name__ == "__main__":
    main()

