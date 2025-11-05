# -*- coding: utf-8 -*-
"""
数据同步服务 - Celery Worker拆分
职责：MongoDB <-> ClickHouse数据同步、缓存预热、定时数据清理
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from celery import Celery
from app.core.service_config import ServiceConfig

# 配置
config = ServiceConfig()

# 创建Celery应用
app = Celery('data-sync',
             broker=f'redis://{config.redis_host}:{config.redis_port}/0',
             backend=f'redis://{config.redis_host}:{config.redis_port}/0')

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # Worker配置
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)


@app.task(name='data_sync.sync_mongodb_to_clickhouse')
def sync_mongodb_to_clickhouse(tenant_id: str, scenario_id: str):
    """同步MongoDB数据到ClickHouse"""
    try:
        print(f"[DataSync] 同步数据: {tenant_id}/{scenario_id}")
        # 这里应该实现实际的同步逻辑
        return {"status": "success", "tenant_id": tenant_id}
    except Exception as e:
        print(f"[DataSync] 同步失败: {e}")
        return {"status": "failed", "error": str(e)}


@app.task(name='data_sync.warm_cache')
def warm_cache(cache_type: str):
    """缓存预热"""
    try:
        print(f"[DataSync] 缓存预热: {cache_type}")
        # 这里应该实现缓存预热逻辑
        return {"status": "success", "cache_type": cache_type}
    except Exception as e:
        print(f"[DataSync] 缓存预热失败: {e}")
        return {"status": "failed", "error": str(e)}


@app.task(name='data_sync.clean_old_data')
def clean_old_data(days: int = 90):
    """清理旧数据"""
    try:
        print(f"[DataSync] 清理{days}天前的旧数据")
        # 这里应该实现数据清理逻辑
        return {"status": "success", "days": days}
    except Exception as e:
        print(f"[DataSync] 清理数据失败: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == '__main__':
    # 启动Worker
    # celery -A services.data-sync.main worker --loglevel=info
    app.start()

