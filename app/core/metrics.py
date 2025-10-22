"""
Prometheus监控指标
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
import time


# ===== 请求指标 =====
# 请求总数
request_count = Counter(
    'recommendation_requests_total',
    'Total recommendation requests',
    ['tenant_id', 'scenario_id', 'endpoint']
)

# 请求延迟
request_latency = Histogram(
    'recommendation_request_duration_seconds',
    'Request latency',
    ['tenant_id', 'scenario_id', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# ===== 推荐指标 =====
# 推荐结果数量
recommendation_items_count = Histogram(
    'recommendation_items_count',
    'Number of recommended items',
    ['tenant_id', 'scenario_id'],
    buckets=[0, 10, 20, 50, 100, 200]
)

# 召回覆盖率
recall_coverage = Gauge(
    'recommendation_recall_coverage',
    'Recall coverage rate',
    ['tenant_id', 'scenario_id', 'strategy']
)

# 推荐多样性
recommendation_diversity = Gauge(
    'recommendation_diversity_score',
    'Recommendation diversity score',
    ['tenant_id', 'scenario_id']
)

# ===== 业务指标 =====
# CTR
ctr_metric = Gauge(
    'recommendation_ctr',
    'Click-through rate',
    ['tenant_id', 'scenario_id']
)

# 缓存命中率
cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate',
    ['cache_type']
)

# ===== 系统信息 =====
app_info = Info('app_info', 'Application info')
app_info.info({'version': '1.0.0', 'name': 'lemo_recommender'})


def track_request_metrics(tenant_id: str, scenario_id: str, endpoint: str):
    """装饰器：跟踪请求指标"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request_count.labels(
                tenant_id=tenant_id,
                scenario_id=scenario_id,
                endpoint=endpoint
            ).inc()
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                request_latency.labels(
                    tenant_id=tenant_id,
                    scenario_id=scenario_id,
                    endpoint=endpoint
                ).observe(duration)
        
        return wrapper
    return decorator
