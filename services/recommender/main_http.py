"""
HTTP 服务启动入口
启动 FastAPI HTTP 服务
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.main import create_app
import uvicorn

from app.core.config import settings


def main():
    """启动 HTTP 服务"""
    app = create_app()
    
    # 从环境变量读取配置（K8s ConfigMap 使用 HTTP_HOST 和 HTTP_PORT）
    host = os.getenv("HTTP_HOST", settings.host)
    port = int(os.getenv("HTTP_PORT", str(settings.port)))
    workers = int(os.getenv("HTTP_WORKERS", str(settings.workers if not settings.debug else 1)))
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers,
        log_level="info" if not settings.debug else "debug"
    )


if __name__ == "__main__":
    main()

