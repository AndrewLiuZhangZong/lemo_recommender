"""
gRPC 服务启动入口
启动 gRPC 服务
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.grpc_server.server import serve
from app.core.config import settings


def main():
    """启动 gRPC 服务"""
    host = "0.0.0.0"
    port = 50051  # TODO: 从配置读取
    
    print("=" * 70)
    print("🚀 启动 gRPC 服务...")
    print("=" * 70)
    print(f"   gRPC 地址: {host}:{port}")
    print("=" * 70)
    
    asyncio.run(serve(host=host, port=port))


if __name__ == "__main__":
    main()

