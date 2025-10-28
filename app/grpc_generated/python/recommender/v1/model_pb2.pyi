from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from recommender_common.v1 import pagination_pb2 as _pagination_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ModelType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MODEL_TYPE_UNSPECIFIED: _ClassVar[ModelType]
    MODEL_TYPE_RECALL: _ClassVar[ModelType]
    MODEL_TYPE_RANK: _ClassVar[ModelType]
    MODEL_TYPE_RERANK: _ClassVar[ModelType]

class ModelStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MODEL_STATUS_UNSPECIFIED: _ClassVar[ModelStatus]
    MODEL_STATUS_TRAINING: _ClassVar[ModelStatus]
    MODEL_STATUS_TRAINED: _ClassVar[ModelStatus]
    MODEL_STATUS_DEPLOYED: _ClassVar[ModelStatus]
    MODEL_STATUS_FAILED: _ClassVar[ModelStatus]
MODEL_TYPE_UNSPECIFIED: ModelType
MODEL_TYPE_RECALL: ModelType
MODEL_TYPE_RANK: ModelType
MODEL_TYPE_RERANK: ModelType
MODEL_STATUS_UNSPECIFIED: ModelStatus
MODEL_STATUS_TRAINING: ModelStatus
MODEL_STATUS_TRAINED: ModelStatus
MODEL_STATUS_DEPLOYED: ModelStatus
MODEL_STATUS_FAILED: ModelStatus

class Model(_message.Message):
    __slots__ = ("id", "tenant_id", "scenario_id", "model_id", "name", "model_type", "algorithm", "version", "status", "config", "metrics", "model_path", "created_at", "updated_at", "trained_at", "deployed_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    MODEL_TYPE_FIELD_NUMBER: _ClassVar[int]
    ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    METRICS_FIELD_NUMBER: _ClassVar[int]
    MODEL_PATH_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    TRAINED_AT_FIELD_NUMBER: _ClassVar[int]
    DEPLOYED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    tenant_id: str
    scenario_id: str
    model_id: str
    name: str
    model_type: ModelType
    algorithm: str
    version: str
    status: ModelStatus
    config: _struct_pb2.Struct
    metrics: _struct_pb2.Struct
    model_path: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    trained_at: _timestamp_pb2.Timestamp
    deployed_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., model_id: _Optional[str] = ..., name: _Optional[str] = ..., model_type: _Optional[_Union[ModelType, str]] = ..., algorithm: _Optional[str] = ..., version: _Optional[str] = ..., status: _Optional[_Union[ModelStatus, str]] = ..., config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., metrics: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., model_path: _Optional[str] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., trained_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., deployed_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreateModelRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "model_id", "name", "model_type", "algorithm", "version", "config")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    MODEL_TYPE_FIELD_NUMBER: _ClassVar[int]
    ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    model_id: str
    name: str
    model_type: ModelType
    algorithm: str
    version: str
    config: _struct_pb2.Struct
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., model_id: _Optional[str] = ..., name: _Optional[str] = ..., model_type: _Optional[_Union[ModelType, str]] = ..., algorithm: _Optional[str] = ..., version: _Optional[str] = ..., config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class CreateModelResponse(_message.Message):
    __slots__ = ("model",)
    MODEL_FIELD_NUMBER: _ClassVar[int]
    model: Model
    def __init__(self, model: _Optional[_Union[Model, _Mapping]] = ...) -> None: ...

class GetModelRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "model_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    model_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., model_id: _Optional[str] = ...) -> None: ...

class GetModelResponse(_message.Message):
    __slots__ = ("model",)
    MODEL_FIELD_NUMBER: _ClassVar[int]
    model: Model
    def __init__(self, model: _Optional[_Union[Model, _Mapping]] = ...) -> None: ...

class ListModelsRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "model_type", "status", "page")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_TYPE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    model_type: ModelType
    status: ModelStatus
    page: _pagination_pb2.PageRequest
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., model_type: _Optional[_Union[ModelType, str]] = ..., status: _Optional[_Union[ModelStatus, str]] = ..., page: _Optional[_Union[_pagination_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class ListModelsResponse(_message.Message):
    __slots__ = ("models", "page_info")
    MODELS_FIELD_NUMBER: _ClassVar[int]
    PAGE_INFO_FIELD_NUMBER: _ClassVar[int]
    models: _containers.RepeatedCompositeFieldContainer[Model]
    page_info: _pagination_pb2.PageInfo
    def __init__(self, models: _Optional[_Iterable[_Union[Model, _Mapping]]] = ..., page_info: _Optional[_Union[_pagination_pb2.PageInfo, _Mapping]] = ...) -> None: ...

class UpdateModelRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "model_id", "name", "config", "status")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    model_id: str
    name: str
    config: _struct_pb2.Struct
    status: ModelStatus
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., model_id: _Optional[str] = ..., name: _Optional[str] = ..., config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., status: _Optional[_Union[ModelStatus, str]] = ...) -> None: ...

class UpdateModelResponse(_message.Message):
    __slots__ = ("model",)
    MODEL_FIELD_NUMBER: _ClassVar[int]
    model: Model
    def __init__(self, model: _Optional[_Union[Model, _Mapping]] = ...) -> None: ...

class DeleteModelRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "model_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    model_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., model_id: _Optional[str] = ...) -> None: ...

class DeleteModelResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class TrainModelRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "model_id", "training_config")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    TRAINING_CONFIG_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    model_id: str
    training_config: _struct_pb2.Struct
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., model_id: _Optional[str] = ..., training_config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class TrainModelResponse(_message.Message):
    __slots__ = ("job_id", "model")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    model: Model
    def __init__(self, job_id: _Optional[str] = ..., model: _Optional[_Union[Model, _Mapping]] = ...) -> None: ...

class GetTrainingStatusRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "model_id", "job_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    model_id: str
    job_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., model_id: _Optional[str] = ..., job_id: _Optional[str] = ...) -> None: ...

class TrainingStatus(_message.Message):
    __slots__ = ("job_id", "status", "progress", "metrics", "error_message", "started_at", "completed_at")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    METRICS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    STARTED_AT_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_AT_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    status: str
    progress: int
    metrics: _struct_pb2.Struct
    error_message: str
    started_at: _timestamp_pb2.Timestamp
    completed_at: _timestamp_pb2.Timestamp
    def __init__(self, job_id: _Optional[str] = ..., status: _Optional[str] = ..., progress: _Optional[int] = ..., metrics: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., error_message: _Optional[str] = ..., started_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., completed_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetTrainingStatusResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: TrainingStatus
    def __init__(self, status: _Optional[_Union[TrainingStatus, _Mapping]] = ...) -> None: ...

class DeployModelRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "model_id", "version")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    model_id: str
    version: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., model_id: _Optional[str] = ..., version: _Optional[str] = ...) -> None: ...

class DeployModelResponse(_message.Message):
    __slots__ = ("model", "deployment_url")
    MODEL_FIELD_NUMBER: _ClassVar[int]
    DEPLOYMENT_URL_FIELD_NUMBER: _ClassVar[int]
    model: Model
    deployment_url: str
    def __init__(self, model: _Optional[_Union[Model, _Mapping]] = ..., deployment_url: _Optional[str] = ...) -> None: ...
