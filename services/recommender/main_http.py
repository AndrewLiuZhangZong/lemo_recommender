"""
HTTP 服务启动入口
启动 FastAPI HTTP 服务
"""
import sys
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
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        workers=settings.workers if not settings.debug else 1,
        log_level="info" if not settings.debug else "debug"
    )


if __name__ == "__main__":
    main()

