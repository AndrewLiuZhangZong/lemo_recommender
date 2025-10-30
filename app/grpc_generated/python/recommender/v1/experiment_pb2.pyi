from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from recommender_common.v1 import pagination_pb2 as _pagination_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExperimentStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EXPERIMENT_STATUS_UNSPECIFIED: _ClassVar[ExperimentStatus]
    EXPERIMENT_STATUS_DRAFT: _ClassVar[ExperimentStatus]
    EXPERIMENT_STATUS_RUNNING: _ClassVar[ExperimentStatus]
    EXPERIMENT_STATUS_PAUSED: _ClassVar[ExperimentStatus]
    EXPERIMENT_STATUS_STOPPED: _ClassVar[ExperimentStatus]
    EXPERIMENT_STATUS_COMPLETED: _ClassVar[ExperimentStatus]

class TrafficSplitMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TRAFFIC_SPLIT_METHOD_UNSPECIFIED: _ClassVar[TrafficSplitMethod]
    TRAFFIC_SPLIT_METHOD_USER_ID_HASH: _ClassVar[TrafficSplitMethod]
    TRAFFIC_SPLIT_METHOD_RANDOM: _ClassVar[TrafficSplitMethod]
    TRAFFIC_SPLIT_METHOD_WEIGHTED: _ClassVar[TrafficSplitMethod]
EXPERIMENT_STATUS_UNSPECIFIED: ExperimentStatus
EXPERIMENT_STATUS_DRAFT: ExperimentStatus
EXPERIMENT_STATUS_RUNNING: ExperimentStatus
EXPERIMENT_STATUS_PAUSED: ExperimentStatus
EXPERIMENT_STATUS_STOPPED: ExperimentStatus
EXPERIMENT_STATUS_COMPLETED: ExperimentStatus
TRAFFIC_SPLIT_METHOD_UNSPECIFIED: TrafficSplitMethod
TRAFFIC_SPLIT_METHOD_USER_ID_HASH: TrafficSplitMethod
TRAFFIC_SPLIT_METHOD_RANDOM: TrafficSplitMethod
TRAFFIC_SPLIT_METHOD_WEIGHTED: TrafficSplitMethod

class Experiment(_message.Message):
    __slots__ = ("id", "tenant_id", "scenario_id", "experiment_id", "name", "description", "hypothesis", "groups", "status", "traffic_split_method", "min_sample_size", "confidence_level", "start_time", "end_time", "created_at", "updated_at", "created_by")
    ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    HYPOTHESIS_FIELD_NUMBER: _ClassVar[int]
    GROUPS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TRAFFIC_SPLIT_METHOD_FIELD_NUMBER: _ClassVar[int]
    MIN_SAMPLE_SIZE_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_LEVEL_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    CREATED_BY_FIELD_NUMBER: _ClassVar[int]
    id: str
    tenant_id: str
    scenario_id: str
    experiment_id: str
    name: str
    description: str
    hypothesis: str
    groups: _containers.RepeatedCompositeFieldContainer[ExperimentGroup]
    status: ExperimentStatus
    traffic_split_method: TrafficSplitMethod
    min_sample_size: int
    confidence_level: float
    start_time: _timestamp_pb2.Timestamp
    end_time: _timestamp_pb2.Timestamp
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    created_by: str
    def __init__(self, id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., experiment_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., hypothesis: _Optional[str] = ..., groups: _Optional[_Iterable[_Union[ExperimentGroup, _Mapping]]] = ..., status: _Optional[_Union[ExperimentStatus, str]] = ..., traffic_split_method: _Optional[_Union[TrafficSplitMethod, str]] = ..., min_sample_size: _Optional[int] = ..., confidence_level: _Optional[float] = ..., start_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., created_by: _Optional[str] = ...) -> None: ...

class ExperimentStrategyConfig(_message.Message):
    __slots__ = ("recall_model_ids", "rank_model_id", "rerank_rule_ids", "additional_config")
    RECALL_MODEL_IDS_FIELD_NUMBER: _ClassVar[int]
    RANK_MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    RERANK_RULE_IDS_FIELD_NUMBER: _ClassVar[int]
    ADDITIONAL_CONFIG_FIELD_NUMBER: _ClassVar[int]
    recall_model_ids: _containers.RepeatedScalarFieldContainer[str]
    rank_model_id: str
    rerank_rule_ids: _containers.RepeatedScalarFieldContainer[str]
    additional_config: _struct_pb2.Struct
    def __init__(self, recall_model_ids: _Optional[_Iterable[str]] = ..., rank_model_id: _Optional[str] = ..., rerank_rule_ids: _Optional[_Iterable[str]] = ..., additional_config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class ExperimentGroup(_message.Message):
    __slots__ = ("group_id", "name", "traffic_ratio", "strategy", "is_control")
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TRAFFIC_RATIO_FIELD_NUMBER: _ClassVar[int]
    STRATEGY_FIELD_NUMBER: _ClassVar[int]
    IS_CONTROL_FIELD_NUMBER: _ClassVar[int]
    group_id: str
    name: str
    traffic_ratio: float
    strategy: ExperimentStrategyConfig
    is_control: bool
    def __init__(self, group_id: _Optional[str] = ..., name: _Optional[str] = ..., traffic_ratio: _Optional[float] = ..., strategy: _Optional[_Union[ExperimentStrategyConfig, _Mapping]] = ..., is_control: bool = ...) -> None: ...

class CreateExperimentRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "name", "description", "hypothesis", "groups", "traffic_split_method", "min_sample_size", "confidence_level", "created_by")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    HYPOTHESIS_FIELD_NUMBER: _ClassVar[int]
    GROUPS_FIELD_NUMBER: _ClassVar[int]
    TRAFFIC_SPLIT_METHOD_FIELD_NUMBER: _ClassVar[int]
    MIN_SAMPLE_SIZE_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_LEVEL_FIELD_NUMBER: _ClassVar[int]
    CREATED_BY_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    name: str
    description: str
    hypothesis: str
    groups: _containers.RepeatedCompositeFieldContainer[ExperimentGroup]
    traffic_split_method: TrafficSplitMethod
    min_sample_size: int
    confidence_level: float
    created_by: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., hypothesis: _Optional[str] = ..., groups: _Optional[_Iterable[_Union[ExperimentGroup, _Mapping]]] = ..., traffic_split_method: _Optional[_Union[TrafficSplitMethod, str]] = ..., min_sample_size: _Optional[int] = ..., confidence_level: _Optional[float] = ..., created_by: _Optional[str] = ...) -> None: ...

class CreateExperimentResponse(_message.Message):
    __slots__ = ("experiment",)
    EXPERIMENT_FIELD_NUMBER: _ClassVar[int]
    experiment: Experiment
    def __init__(self, experiment: _Optional[_Union[Experiment, _Mapping]] = ...) -> None: ...

class GetExperimentRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "experiment_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    experiment_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., experiment_id: _Optional[str] = ...) -> None: ...

class GetExperimentResponse(_message.Message):
    __slots__ = ("experiment",)
    EXPERIMENT_FIELD_NUMBER: _ClassVar[int]
    experiment: Experiment
    def __init__(self, experiment: _Optional[_Union[Experiment, _Mapping]] = ...) -> None: ...

class ListExperimentsRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "status", "page")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    status: ExperimentStatus
    page: _pagination_pb2.PageRequest
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., status: _Optional[_Union[ExperimentStatus, str]] = ..., page: _Optional[_Union[_pagination_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class ListExperimentsResponse(_message.Message):
    __slots__ = ("experiments", "page_info")
    EXPERIMENTS_FIELD_NUMBER: _ClassVar[int]
    PAGE_INFO_FIELD_NUMBER: _ClassVar[int]
    experiments: _containers.RepeatedCompositeFieldContainer[Experiment]
    page_info: _pagination_pb2.PageInfo
    def __init__(self, experiments: _Optional[_Iterable[_Union[Experiment, _Mapping]]] = ..., page_info: _Optional[_Union[_pagination_pb2.PageInfo, _Mapping]] = ...) -> None: ...

class UpdateExperimentRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "experiment_id", "name", "description", "hypothesis", "min_sample_size", "confidence_level")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    HYPOTHESIS_FIELD_NUMBER: _ClassVar[int]
    MIN_SAMPLE_SIZE_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_LEVEL_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    experiment_id: str
    name: str
    description: str
    hypothesis: str
    min_sample_size: int
    confidence_level: float
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., experiment_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., hypothesis: _Optional[str] = ..., min_sample_size: _Optional[int] = ..., confidence_level: _Optional[float] = ...) -> None: ...

class UpdateExperimentResponse(_message.Message):
    __slots__ = ("experiment",)
    EXPERIMENT_FIELD_NUMBER: _ClassVar[int]
    experiment: Experiment
    def __init__(self, experiment: _Optional[_Union[Experiment, _Mapping]] = ...) -> None: ...

class DeleteExperimentRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "experiment_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    experiment_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., experiment_id: _Optional[str] = ...) -> None: ...

class DeleteExperimentResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class StartExperimentRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "experiment_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    experiment_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., experiment_id: _Optional[str] = ...) -> None: ...

class StartExperimentResponse(_message.Message):
    __slots__ = ("experiment",)
    EXPERIMENT_FIELD_NUMBER: _ClassVar[int]
    experiment: Experiment
    def __init__(self, experiment: _Optional[_Union[Experiment, _Mapping]] = ...) -> None: ...

class StopExperimentRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "experiment_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    experiment_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., experiment_id: _Optional[str] = ...) -> None: ...

class StopExperimentResponse(_message.Message):
    __slots__ = ("experiment",)
    EXPERIMENT_FIELD_NUMBER: _ClassVar[int]
    experiment: Experiment
    def __init__(self, experiment: _Optional[_Union[Experiment, _Mapping]] = ...) -> None: ...

class GetExperimentResultsRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "experiment_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    experiment_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., experiment_id: _Optional[str] = ...) -> None: ...

class ExperimentResult(_message.Message):
    __slots__ = ("group_id", "group_name", "metrics", "sample_size", "confidence", "is_significant")
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    GROUP_NAME_FIELD_NUMBER: _ClassVar[int]
    METRICS_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_SIZE_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    IS_SIGNIFICANT_FIELD_NUMBER: _ClassVar[int]
    group_id: str
    group_name: str
    metrics: _struct_pb2.Struct
    sample_size: int
    confidence: float
    is_significant: bool
    def __init__(self, group_id: _Optional[str] = ..., group_name: _Optional[str] = ..., metrics: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., sample_size: _Optional[int] = ..., confidence: _Optional[float] = ..., is_significant: bool = ...) -> None: ...

class GetExperimentResultsResponse(_message.Message):
    __slots__ = ("experiment", "results", "summary")
    EXPERIMENT_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    experiment: Experiment
    results: _containers.RepeatedCompositeFieldContainer[ExperimentResult]
    summary: _struct_pb2.Struct
    def __init__(self, experiment: _Optional[_Union[Experiment, _Mapping]] = ..., results: _Optional[_Iterable[_Union[ExperimentResult, _Mapping]]] = ..., summary: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...
