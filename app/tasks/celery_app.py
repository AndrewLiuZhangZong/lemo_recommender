"""
Celery应用配置
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings


# 创建Celery应用
celery_app = Celery(
    "lemo_recommender",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.item_tasks",
        "app.tasks.user_tasks",
        "app.tasks.model_tasks",
        "app.tasks.recommendation_tasks"
    ]
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    task_soft_time_limit=3300,  # 55分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    # 每小时计算物品相似度
    "compute-item-similarity-hourly": {
        "task": "app.tasks.item_tasks.compute_item_similarity",
        "schedule": crontab(minute=0),  # 每小时
        "args": (),
    },
    # 每2小时更新用户画像
    "update-user-profiles-2hours": {
        "task": "app.tasks.user_tasks.update_user_profiles_batch",
        "schedule": crontab(minute=0, hour="*/2"),  # 每2小时
        "args": (),
    },
    # 每天凌晨3点训练模型
    "train-model-daily": {
        "task": "app.tasks.model_tasks.train_model_daily",
        "schedule": crontab(minute=0, hour=3),  # 每天3:00
        "args": (),
    },
    # 每4小时预计算推荐结果
    "precompute-recommendations-4hours": {
        "task": "app.tasks.recommendation_tasks.precompute_recommendations",
        "schedule": crontab(minute=0, hour="*/4"),  # 每4小时
        "args": (),
    },
    # 每天凌晨4点清理过期缓存
    "cleanup-expired-cache-daily": {
        "task": "app.tasks.recommendation_tasks.cleanup_expired_cache",
        "schedule": crontab(minute=0, hour=4),  # 每天4:00
        "args": (),
    },
}


if __name__ == '__main__':
    celery_app.start()

