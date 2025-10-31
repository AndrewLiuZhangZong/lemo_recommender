"""
Celery Beat 服务启动入口
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.tasks.celery_app import celery_app


def main():
    """启动 Celery Beat"""
    print("=" * 70)
    print("🚀 启动 Celery Beat...")
    print("=" * 70)
    
    celery_app.start()


if __name__ == "__main__":
    # 使用 celery 命令行工具启动
    # celery -A app.tasks.celery_app beat -l info --scheduler redbeat.RedBeatScheduler
    print("使用命令启动: celery -A app.tasks.celery_app beat -l info --scheduler redbeat.RedBeatScheduler")
    print("或使用 K8s Deployment 中的 command 配置")
    
    # 如果需要直接启动
    main()

