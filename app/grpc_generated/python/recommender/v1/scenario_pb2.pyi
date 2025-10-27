from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from common.v1 import pagination_pb2 as _pagination_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Scenario(_message.Message):
    __slots__ = ("id", "tenant_id", "scenario_id", "name", "scenario_type", "description", "config", "status", "created_at", "updated_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    tenant_id: str
    scenario_id: str
    name: str
    scenario_type: str
    description: str
    config: _struct_pb2.Struct
    status: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., name: _Optional[str] = ..., scenario_type: _Optional[str] = ..., description: _Optional[str] = ..., config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., status: _Optional[str] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreateScenarioRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "name", "scenario_type", "description", "config")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    name: str
    scenario_type: str
    description: str
    config: _struct_pb2.Struct
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., name: _Optional[str] = ..., scenario_type: _Optional[str] = ..., description: _Optional[str] = ..., config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class CreateScenarioResponse(_message.Message):
    __slots__ = ("scenario",)
    SCENARIO_FIELD_NUMBER: _ClassVar[int]
    scenario: Scenario
    def __init__(self, scenario: _Optional[_Union[Scenario, _Mapping]] = ...) -> None: ...

class GetScenarioRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ...) -> None: ...

class GetScenarioResponse(_message.Message):
    __slots__ = ("scenario",)
    SCENARIO_FIELD_NUMBER: _ClassVar[int]
    scenario: Scenario
    def __init__(self, scenario: _Optional[_Union[Scenario, _Mapping]] = ...) -> None: ...

class ListScenariosRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_type", "status", "page")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_TYPE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_type: str
    status: str
    page: _pagination_pb2.PageRequest
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_type: _Optional[str] = ..., status: _Optional[str] = ..., page: _Optional[_Union[_pagination_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class ListScenariosResponse(_message.Message):
    __slots__ = ("scenarios", "page_info")
    SCENARIOS_FIELD_NUMBER: _ClassVar[int]
    PAGE_INFO_FIELD_NUMBER: _ClassVar[int]
    scenarios: _containers.RepeatedCompositeFieldContainer[Scenario]
    page_info: _pagination_pb2.PageInfo
    def __init__(self, scenarios: _Optional[_Iterable[_Union[Scenario, _Mapping]]] = ..., page_info: _Optional[_Union[_pagination_pb2.PageInfo, _Mapping]] = ...) -> None: ...

class UpdateScenarioRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "name", "description", "config")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    name: str
    description: str
    config: _struct_pb2.Struct
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class UpdateScenarioResponse(_message.Message):
    __slots__ = ("scenario",)
    SCENARIO_FIELD_NUMBER: _ClassVar[int]
    scenario: Scenario
    def __init__(self, scenario: _Optional[_Union[Scenario, _Mapping]] = ...) -> None: ...

class DeleteScenarioRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ...) -> None: ...

class DeleteScenarioResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class UpdateScenarioStatusRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "status")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    status: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., status: _Optional[str] = ...) -> None: ...

class UpdateScenarioStatusResponse(_message.Message):
    __slots__ = ("scenario",)
    SCENARIO_FIELD_NUMBER: _ClassVar[int]
    scenario: Scenario
    def __init__(self, scenario: _Optional[_Union[Scenario, _Mapping]] = ...) -> None: ...
