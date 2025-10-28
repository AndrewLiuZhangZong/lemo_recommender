from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from recommender_common.v1 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetDashboardRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "time_range")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    TIME_RANGE_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    time_range: _common_pb2.TimeRange
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., time_range: _Optional[_Union[_common_pb2.TimeRange, _Mapping]] = ...) -> None: ...

class DashboardData(_message.Message):
    __slots__ = ("total_recommendations", "total_clicks", "ctr", "total_users", "active_users", "total_items", "avg_response_time", "cache_hit_rate")
    TOTAL_RECOMMENDATIONS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CLICKS_FIELD_NUMBER: _ClassVar[int]
    CTR_FIELD_NUMBER: _ClassVar[int]
    TOTAL_USERS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_USERS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_ITEMS_FIELD_NUMBER: _ClassVar[int]
    AVG_RESPONSE_TIME_FIELD_NUMBER: _ClassVar[int]
    CACHE_HIT_RATE_FIELD_NUMBER: _ClassVar[int]
    total_recommendations: int
    total_clicks: int
    ctr: float
    total_users: int
    active_users: int
    total_items: int
    avg_response_time: float
    cache_hit_rate: float
    def __init__(self, total_recommendations: _Optional[int] = ..., total_clicks: _Optional[int] = ..., ctr: _Optional[float] = ..., total_users: _Optional[int] = ..., active_users: _Optional[int] = ..., total_items: _Optional[int] = ..., avg_response_time: _Optional[float] = ..., cache_hit_rate: _Optional[float] = ...) -> None: ...

class GetDashboardResponse(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: DashboardData
    def __init__(self, data: _Optional[_Union[DashboardData, _Mapping]] = ...) -> None: ...

class GetMetricsTrendRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "metrics", "time_range", "granularity")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    METRICS_FIELD_NUMBER: _ClassVar[int]
    TIME_RANGE_FIELD_NUMBER: _ClassVar[int]
    GRANULARITY_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    metrics: _containers.RepeatedScalarFieldContainer[str]
    time_range: _common_pb2.TimeRange
    granularity: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., metrics: _Optional[_Iterable[str]] = ..., time_range: _Optional[_Union[_common_pb2.TimeRange, _Mapping]] = ..., granularity: _Optional[str] = ...) -> None: ...

class TimeSeriesPoint(_message.Message):
    __slots__ = ("timestamp", "value")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    value: float
    def __init__(self, timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., value: _Optional[float] = ...) -> None: ...

class MetricTrend(_message.Message):
    __slots__ = ("metric_name", "points")
    METRIC_NAME_FIELD_NUMBER: _ClassVar[int]
    POINTS_FIELD_NUMBER: _ClassVar[int]
    metric_name: str
    points: _containers.RepeatedCompositeFieldContainer[TimeSeriesPoint]
    def __init__(self, metric_name: _Optional[str] = ..., points: _Optional[_Iterable[_Union[TimeSeriesPoint, _Mapping]]] = ...) -> None: ...

class GetMetricsTrendResponse(_message.Message):
    __slots__ = ("trends",)
    TRENDS_FIELD_NUMBER: _ClassVar[int]
    trends: _containers.RepeatedCompositeFieldContainer[MetricTrend]
    def __init__(self, trends: _Optional[_Iterable[_Union[MetricTrend, _Mapping]]] = ...) -> None: ...

class GetItemDistributionRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "dimension")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    DIMENSION_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    dimension: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., dimension: _Optional[str] = ...) -> None: ...

class DistributionData(_message.Message):
    __slots__ = ("label", "count", "percentage")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
    label: str
    count: int
    percentage: float
    def __init__(self, label: _Optional[str] = ..., count: _Optional[int] = ..., percentage: _Optional[float] = ...) -> None: ...

class GetItemDistributionResponse(_message.Message):
    __slots__ = ("distribution",)
    DISTRIBUTION_FIELD_NUMBER: _ClassVar[int]
    distribution: _containers.RepeatedCompositeFieldContainer[DistributionData]
    def __init__(self, distribution: _Optional[_Iterable[_Union[DistributionData, _Mapping]]] = ...) -> None: ...

class GetUserBehaviorAnalysisRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "time_range")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    TIME_RANGE_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    time_range: _common_pb2.TimeRange
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., time_range: _Optional[_Union[_common_pb2.TimeRange, _Mapping]] = ...) -> None: ...

class BehaviorStats(_message.Message):
    __slots__ = ("action_type", "count", "unique_users")
    ACTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    UNIQUE_USERS_FIELD_NUMBER: _ClassVar[int]
    action_type: str
    count: int
    unique_users: int
    def __init__(self, action_type: _Optional[str] = ..., count: _Optional[int] = ..., unique_users: _Optional[int] = ...) -> None: ...

class GetUserBehaviorAnalysisResponse(_message.Message):
    __slots__ = ("stats", "funnel_data")
    STATS_FIELD_NUMBER: _ClassVar[int]
    FUNNEL_DATA_FIELD_NUMBER: _ClassVar[int]
    stats: _containers.RepeatedCompositeFieldContainer[BehaviorStats]
    funnel_data: _struct_pb2.Struct
    def __init__(self, stats: _Optional[_Iterable[_Union[BehaviorStats, _Mapping]]] = ..., funnel_data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class ExportDataRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "data_type", "time_range", "format")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    DATA_TYPE_FIELD_NUMBER: _ClassVar[int]
    TIME_RANGE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    data_type: str
    time_range: _common_pb2.TimeRange
    format: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., data_type: _Optional[str] = ..., time_range: _Optional[_Union[_common_pb2.TimeRange, _Mapping]] = ..., format: _Optional[str] = ...) -> None: ...

class ExportDataResponse(_message.Message):
    __slots__ = ("download_url", "file_name", "record_count", "expires_at")
    DOWNLOAD_URL_FIELD_NUMBER: _ClassVar[int]
    FILE_NAME_FIELD_NUMBER: _ClassVar[int]
    RECORD_COUNT_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    download_url: str
    file_name: str
    record_count: int
    expires_at: _timestamp_pb2.Timestamp
    def __init__(self, download_url: _Optional[str] = ..., file_name: _Optional[str] = ..., record_count: _Optional[int] = ..., expires_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
