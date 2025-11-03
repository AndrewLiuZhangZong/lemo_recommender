from recommender_common.v1 import common_pb2 as _common_pb2
from recommender_common.v1 import pagination_pb2 as _pagination_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class JobTemplateType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    JOB_TEMPLATE_TYPE_UNSPECIFIED: _ClassVar[JobTemplateType]
    PYTHON_SCRIPT: _ClassVar[JobTemplateType]
    JAR: _ClassVar[JobTemplateType]
    SQL: _ClassVar[JobTemplateType]
    PYTHON_FLINK: _ClassVar[JobTemplateType]

class JobStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    JOB_STATUS_UNSPECIFIED: _ClassVar[JobStatus]
    CREATED: _ClassVar[JobStatus]
    RUNNING: _ClassVar[JobStatus]
    FINISHED: _ClassVar[JobStatus]
    FAILED: _ClassVar[JobStatus]
    CANCELLED: _ClassVar[JobStatus]
    SUSPENDED: _ClassVar[JobStatus]
    RECONCILING: _ClassVar[JobStatus]
JOB_TEMPLATE_TYPE_UNSPECIFIED: JobTemplateType
PYTHON_SCRIPT: JobTemplateType
JAR: JobTemplateType
SQL: JobTemplateType
PYTHON_FLINK: JobTemplateType
JOB_STATUS_UNSPECIFIED: JobStatus
CREATED: JobStatus
RUNNING: JobStatus
FINISHED: JobStatus
FAILED: JobStatus
CANCELLED: JobStatus
SUSPENDED: JobStatus
RECONCILING: JobStatus

class JobTemplate(_message.Message):
    __slots__ = ("template_id", "name", "description", "job_type", "config", "parallelism", "checkpoints_enabled", "checkpoint_interval_ms", "savepoint_path", "task_manager_memory", "job_manager_memory", "status", "tags", "created_by", "created_at", "updated_at")
    TEMPLATE_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    JOB_TYPE_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    PARALLELISM_FIELD_NUMBER: _ClassVar[int]
    CHECKPOINTS_ENABLED_FIELD_NUMBER: _ClassVar[int]
    CHECKPOINT_INTERVAL_MS_FIELD_NUMBER: _ClassVar[int]
    SAVEPOINT_PATH_FIELD_NUMBER: _ClassVar[int]
    TASK_MANAGER_MEMORY_FIELD_NUMBER: _ClassVar[int]
    JOB_MANAGER_MEMORY_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    CREATED_BY_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    template_id: str
    name: str
    description: str
    job_type: JobTemplateType
    config: _struct_pb2.Struct
    parallelism: int
    checkpoints_enabled: bool
    checkpoint_interval_ms: int
    savepoint_path: str
    task_manager_memory: str
    job_manager_memory: str
    status: str
    tags: _containers.RepeatedScalarFieldContainer[str]
    created_by: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    def __init__(self, template_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., job_type: _Optional[_Union[JobTemplateType, str]] = ..., config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., parallelism: _Optional[int] = ..., checkpoints_enabled: bool = ..., checkpoint_interval_ms: _Optional[int] = ..., savepoint_path: _Optional[str] = ..., task_manager_memory: _Optional[str] = ..., job_manager_memory: _Optional[str] = ..., status: _Optional[str] = ..., tags: _Optional[_Iterable[str]] = ..., created_by: _Optional[str] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class FlinkJob(_message.Message):
    __slots__ = ("job_id", "job_name", "template_id", "flink_job_id", "flink_cluster_url", "status", "error_message", "job_config", "submitted_by", "submitted_at", "start_time", "end_time", "duration", "num_operators", "num_vertices")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    JOB_NAME_FIELD_NUMBER: _ClassVar[int]
    TEMPLATE_ID_FIELD_NUMBER: _ClassVar[int]
    FLINK_JOB_ID_FIELD_NUMBER: _ClassVar[int]
    FLINK_CLUSTER_URL_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    JOB_CONFIG_FIELD_NUMBER: _ClassVar[int]
    SUBMITTED_BY_FIELD_NUMBER: _ClassVar[int]
    SUBMITTED_AT_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    NUM_OPERATORS_FIELD_NUMBER: _ClassVar[int]
    NUM_VERTICES_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    job_name: str
    template_id: str
    flink_job_id: str
    flink_cluster_url: str
    status: JobStatus
    error_message: str
    job_config: _struct_pb2.Struct
    submitted_by: str
    submitted_at: _timestamp_pb2.Timestamp
    start_time: _timestamp_pb2.Timestamp
    end_time: _timestamp_pb2.Timestamp
    duration: int
    num_operators: int
    num_vertices: int
    def __init__(self, job_id: _Optional[str] = ..., job_name: _Optional[str] = ..., template_id: _Optional[str] = ..., flink_job_id: _Optional[str] = ..., flink_cluster_url: _Optional[str] = ..., status: _Optional[_Union[JobStatus, str]] = ..., error_message: _Optional[str] = ..., job_config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., submitted_by: _Optional[str] = ..., submitted_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., start_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., end_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., duration: _Optional[int] = ..., num_operators: _Optional[int] = ..., num_vertices: _Optional[int] = ...) -> None: ...

class CreateJobTemplateRequest(_message.Message):
    __slots__ = ("template_id", "name", "description", "job_type", "config", "parallelism", "checkpoints_enabled", "checkpoint_interval_ms", "task_manager_memory", "job_manager_memory", "tags")
    TEMPLATE_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    JOB_TYPE_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    PARALLELISM_FIELD_NUMBER: _ClassVar[int]
    CHECKPOINTS_ENABLED_FIELD_NUMBER: _ClassVar[int]
    CHECKPOINT_INTERVAL_MS_FIELD_NUMBER: _ClassVar[int]
    TASK_MANAGER_MEMORY_FIELD_NUMBER: _ClassVar[int]
    JOB_MANAGER_MEMORY_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    template_id: str
    name: str
    description: str
    job_type: JobTemplateType
    config: _struct_pb2.Struct
    parallelism: int
    checkpoints_enabled: bool
    checkpoint_interval_ms: int
    task_manager_memory: str
    job_manager_memory: str
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, template_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., job_type: _Optional[_Union[JobTemplateType, str]] = ..., config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., parallelism: _Optional[int] = ..., checkpoints_enabled: bool = ..., checkpoint_interval_ms: _Optional[int] = ..., task_manager_memory: _Optional[str] = ..., job_manager_memory: _Optional[str] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...

class CreateJobTemplateResponse(_message.Message):
    __slots__ = ("template",)
    TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    template: JobTemplate
    def __init__(self, template: _Optional[_Union[JobTemplate, _Mapping]] = ...) -> None: ...

class UpdateJobTemplateRequest(_message.Message):
    __slots__ = ("template_id", "name", "description", "job_type", "config", "parallelism", "checkpoints_enabled", "checkpoint_interval_ms", "task_manager_memory", "job_manager_memory", "tags")
    TEMPLATE_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    JOB_TYPE_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    PARALLELISM_FIELD_NUMBER: _ClassVar[int]
    CHECKPOINTS_ENABLED_FIELD_NUMBER: _ClassVar[int]
    CHECKPOINT_INTERVAL_MS_FIELD_NUMBER: _ClassVar[int]
    TASK_MANAGER_MEMORY_FIELD_NUMBER: _ClassVar[int]
    JOB_MANAGER_MEMORY_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    template_id: str
    name: str
    description: str
    job_type: JobTemplateType
    config: _struct_pb2.Struct
    parallelism: int
    checkpoints_enabled: bool
    checkpoint_interval_ms: int
    task_manager_memory: str
    job_manager_memory: str
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, template_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., job_type: _Optional[_Union[JobTemplateType, str]] = ..., config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., parallelism: _Optional[int] = ..., checkpoints_enabled: bool = ..., checkpoint_interval_ms: _Optional[int] = ..., task_manager_memory: _Optional[str] = ..., job_manager_memory: _Optional[str] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...

class UpdateJobTemplateResponse(_message.Message):
    __slots__ = ("template",)
    TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    template: JobTemplate
    def __init__(self, template: _Optional[_Union[JobTemplate, _Mapping]] = ...) -> None: ...

class DeleteJobTemplateRequest(_message.Message):
    __slots__ = ("template_id",)
    TEMPLATE_ID_FIELD_NUMBER: _ClassVar[int]
    template_id: str
    def __init__(self, template_id: _Optional[str] = ...) -> None: ...

class DeleteJobTemplateResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class GetJobTemplateRequest(_message.Message):
    __slots__ = ("template_id",)
    TEMPLATE_ID_FIELD_NUMBER: _ClassVar[int]
    template_id: str
    def __init__(self, template_id: _Optional[str] = ...) -> None: ...

class GetJobTemplateResponse(_message.Message):
    __slots__ = ("template",)
    TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    template: JobTemplate
    def __init__(self, template: _Optional[_Union[JobTemplate, _Mapping]] = ...) -> None: ...

class ListJobTemplatesRequest(_message.Message):
    __slots__ = ("status", "page", "page_size")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    status: str
    page: int
    page_size: int
    def __init__(self, status: _Optional[str] = ..., page: _Optional[int] = ..., page_size: _Optional[int] = ...) -> None: ...

class ListJobTemplatesResponse(_message.Message):
    __slots__ = ("templates", "page_info")
    TEMPLATES_FIELD_NUMBER: _ClassVar[int]
    PAGE_INFO_FIELD_NUMBER: _ClassVar[int]
    templates: _containers.RepeatedCompositeFieldContainer[JobTemplate]
    page_info: _pagination_pb2.PageInfo
    def __init__(self, templates: _Optional[_Iterable[_Union[JobTemplate, _Mapping]]] = ..., page_info: _Optional[_Union[_pagination_pb2.PageInfo, _Mapping]] = ...) -> None: ...

class SubmitJobRequest(_message.Message):
    __slots__ = ("template_id", "job_id", "job_name", "job_config", "flink_cluster_url", "savepoint_path")
    TEMPLATE_ID_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    JOB_NAME_FIELD_NUMBER: _ClassVar[int]
    JOB_CONFIG_FIELD_NUMBER: _ClassVar[int]
    FLINK_CLUSTER_URL_FIELD_NUMBER: _ClassVar[int]
    SAVEPOINT_PATH_FIELD_NUMBER: _ClassVar[int]
    template_id: str
    job_id: str
    job_name: str
    job_config: _struct_pb2.Struct
    flink_cluster_url: str
    savepoint_path: str
    def __init__(self, template_id: _Optional[str] = ..., job_id: _Optional[str] = ..., job_name: _Optional[str] = ..., job_config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., flink_cluster_url: _Optional[str] = ..., savepoint_path: _Optional[str] = ...) -> None: ...

class SubmitJobResponse(_message.Message):
    __slots__ = ("job",)
    JOB_FIELD_NUMBER: _ClassVar[int]
    job: FlinkJob
    def __init__(self, job: _Optional[_Union[FlinkJob, _Mapping]] = ...) -> None: ...

class GetJobRequest(_message.Message):
    __slots__ = ("job_id",)
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    def __init__(self, job_id: _Optional[str] = ...) -> None: ...

class GetJobResponse(_message.Message):
    __slots__ = ("job",)
    JOB_FIELD_NUMBER: _ClassVar[int]
    job: FlinkJob
    def __init__(self, job: _Optional[_Union[FlinkJob, _Mapping]] = ...) -> None: ...

class ListJobsRequest(_message.Message):
    __slots__ = ("status", "page", "page_size")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    status: str
    page: int
    page_size: int
    def __init__(self, status: _Optional[str] = ..., page: _Optional[int] = ..., page_size: _Optional[int] = ...) -> None: ...

class ListJobsResponse(_message.Message):
    __slots__ = ("jobs", "page_info")
    JOBS_FIELD_NUMBER: _ClassVar[int]
    PAGE_INFO_FIELD_NUMBER: _ClassVar[int]
    jobs: _containers.RepeatedCompositeFieldContainer[FlinkJob]
    page_info: _pagination_pb2.PageInfo
    def __init__(self, jobs: _Optional[_Iterable[_Union[FlinkJob, _Mapping]]] = ..., page_info: _Optional[_Union[_pagination_pb2.PageInfo, _Mapping]] = ...) -> None: ...

class StopJobRequest(_message.Message):
    __slots__ = ("job_id", "force")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    FORCE_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    force: bool
    def __init__(self, job_id: _Optional[str] = ..., force: bool = ...) -> None: ...

class StopJobResponse(_message.Message):
    __slots__ = ("job",)
    JOB_FIELD_NUMBER: _ClassVar[int]
    job: FlinkJob
    def __init__(self, job: _Optional[_Union[FlinkJob, _Mapping]] = ...) -> None: ...

class PauseJobRequest(_message.Message):
    __slots__ = ("job_id",)
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    def __init__(self, job_id: _Optional[str] = ...) -> None: ...

class PauseJobResponse(_message.Message):
    __slots__ = ("job",)
    JOB_FIELD_NUMBER: _ClassVar[int]
    job: FlinkJob
    def __init__(self, job: _Optional[_Union[FlinkJob, _Mapping]] = ...) -> None: ...

class ResumeJobRequest(_message.Message):
    __slots__ = ("job_id", "savepoint_path")
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    SAVEPOINT_PATH_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    savepoint_path: str
    def __init__(self, job_id: _Optional[str] = ..., savepoint_path: _Optional[str] = ...) -> None: ...

class ResumeJobResponse(_message.Message):
    __slots__ = ("job",)
    JOB_FIELD_NUMBER: _ClassVar[int]
    job: FlinkJob
    def __init__(self, job: _Optional[_Union[FlinkJob, _Mapping]] = ...) -> None: ...

class GetClusterInfoRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetClusterInfoResponse(_message.Message):
    __slots__ = ("cluster_info",)
    CLUSTER_INFO_FIELD_NUMBER: _ClassVar[int]
    cluster_info: _struct_pb2.Struct
    def __init__(self, cluster_info: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class ListClusterJobsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListClusterJobsResponse(_message.Message):
    __slots__ = ("jobs",)
    JOBS_FIELD_NUMBER: _ClassVar[int]
    jobs: _containers.RepeatedCompositeFieldContainer[_struct_pb2.Struct]
    def __init__(self, jobs: _Optional[_Iterable[_Union[_struct_pb2.Struct, _Mapping]]] = ...) -> None: ...
