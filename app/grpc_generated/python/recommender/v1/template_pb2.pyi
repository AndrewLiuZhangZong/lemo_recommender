from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from recommender_common.v1 import pagination_pb2 as _pagination_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Template(_message.Message):
    __slots__ = ("id", "template_id", "name", "description", "scenario_types", "config", "is_system", "creator", "created_at", "updated_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    TEMPLATE_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_TYPES_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    IS_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    CREATOR_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    template_id: str
    name: str
    description: str
    scenario_types: _containers.RepeatedScalarFieldContainer[str]
    config: _struct_pb2.Struct
    is_system: bool
    creator: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., template_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., scenario_types: _Optional[_Iterable[str]] = ..., config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., is_system: bool = ..., creator: _Optional[str] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreateTemplateRequest(_message.Message):
    __slots__ = ("template_id", "name", "description", "scenario_types", "config", "creator")
    TEMPLATE_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_TYPES_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    CREATOR_FIELD_NUMBER: _ClassVar[int]
    template_id: str
    name: str
    description: str
    scenario_types: _containers.RepeatedScalarFieldContainer[str]
    config: _struct_pb2.Struct
    creator: str
    def __init__(self, template_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., scenario_types: _Optional[_Iterable[str]] = ..., config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., creator: _Optional[str] = ...) -> None: ...

class CreateTemplateResponse(_message.Message):
    __slots__ = ("template",)
    TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    template: Template
    def __init__(self, template: _Optional[_Union[Template, _Mapping]] = ...) -> None: ...

class GetTemplateRequest(_message.Message):
    __slots__ = ("template_id",)
    TEMPLATE_ID_FIELD_NUMBER: _ClassVar[int]
    template_id: str
    def __init__(self, template_id: _Optional[str] = ...) -> None: ...

class GetTemplateResponse(_message.Message):
    __slots__ = ("template",)
    TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    template: Template
    def __init__(self, template: _Optional[_Union[Template, _Mapping]] = ...) -> None: ...

class ListTemplatesRequest(_message.Message):
    __slots__ = ("scenario_type", "is_system", "page")
    SCENARIO_TYPE_FIELD_NUMBER: _ClassVar[int]
    IS_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    scenario_type: str
    is_system: bool
    page: _pagination_pb2.PageRequest
    def __init__(self, scenario_type: _Optional[str] = ..., is_system: bool = ..., page: _Optional[_Union[_pagination_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class ListTemplatesResponse(_message.Message):
    __slots__ = ("templates", "page_info")
    TEMPLATES_FIELD_NUMBER: _ClassVar[int]
    PAGE_INFO_FIELD_NUMBER: _ClassVar[int]
    templates: _containers.RepeatedCompositeFieldContainer[Template]
    page_info: _pagination_pb2.PageInfo
    def __init__(self, templates: _Optional[_Iterable[_Union[Template, _Mapping]]] = ..., page_info: _Optional[_Union[_pagination_pb2.PageInfo, _Mapping]] = ...) -> None: ...

class UpdateTemplateRequest(_message.Message):
    __slots__ = ("template_id", "name", "description", "scenario_types", "config")
    TEMPLATE_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_TYPES_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    template_id: str
    name: str
    description: str
    scenario_types: _containers.RepeatedScalarFieldContainer[str]
    config: _struct_pb2.Struct
    def __init__(self, template_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., scenario_types: _Optional[_Iterable[str]] = ..., config: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class UpdateTemplateResponse(_message.Message):
    __slots__ = ("template",)
    TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    template: Template
    def __init__(self, template: _Optional[_Union[Template, _Mapping]] = ...) -> None: ...

class DeleteTemplateRequest(_message.Message):
    __slots__ = ("template_id",)
    TEMPLATE_ID_FIELD_NUMBER: _ClassVar[int]
    template_id: str
    def __init__(self, template_id: _Optional[str] = ...) -> None: ...

class DeleteTemplateResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class GetTemplateByScenarioTypeRequest(_message.Message):
    __slots__ = ("scenario_type",)
    SCENARIO_TYPE_FIELD_NUMBER: _ClassVar[int]
    scenario_type: str
    def __init__(self, scenario_type: _Optional[str] = ...) -> None: ...

class GetTemplateByScenarioTypeResponse(_message.Message):
    __slots__ = ("template",)
    TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    template: Template
    def __init__(self, template: _Optional[_Union[Template, _Mapping]] = ...) -> None: ...
