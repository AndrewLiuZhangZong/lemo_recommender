from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ErrorCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ERROR_CODE_UNSPECIFIED: _ClassVar[ErrorCode]
    ERROR_CODE_INTERNAL: _ClassVar[ErrorCode]
    ERROR_CODE_INVALID_ARGUMENT: _ClassVar[ErrorCode]
    ERROR_CODE_NOT_FOUND: _ClassVar[ErrorCode]
    ERROR_CODE_ALREADY_EXISTS: _ClassVar[ErrorCode]
    ERROR_CODE_PERMISSION_DENIED: _ClassVar[ErrorCode]
    ERROR_CODE_UNAUTHENTICATED: _ClassVar[ErrorCode]
    ERROR_CODE_RESOURCE_EXHAUSTED: _ClassVar[ErrorCode]
    ERROR_CODE_FAILED_PRECONDITION: _ClassVar[ErrorCode]
    ERROR_CODE_ABORTED: _ClassVar[ErrorCode]
    ERROR_CODE_OUT_OF_RANGE: _ClassVar[ErrorCode]
    ERROR_CODE_UNIMPLEMENTED: _ClassVar[ErrorCode]
    ERROR_CODE_UNAVAILABLE: _ClassVar[ErrorCode]
    ERROR_CODE_DEADLINE_EXCEEDED: _ClassVar[ErrorCode]
    ERROR_CODE_SCENARIO_NOT_FOUND: _ClassVar[ErrorCode]
    ERROR_CODE_ITEM_NOT_FOUND: _ClassVar[ErrorCode]
    ERROR_CODE_EXPERIMENT_NOT_FOUND: _ClassVar[ErrorCode]
    ERROR_CODE_MODEL_NOT_FOUND: _ClassVar[ErrorCode]
    ERROR_CODE_INVALID_SCENARIO_CONFIG: _ClassVar[ErrorCode]
    ERROR_CODE_RECALL_FAILED: _ClassVar[ErrorCode]
    ERROR_CODE_RANK_FAILED: _ClassVar[ErrorCode]
    ERROR_CODE_RERANK_FAILED: _ClassVar[ErrorCode]
ERROR_CODE_UNSPECIFIED: ErrorCode
ERROR_CODE_INTERNAL: ErrorCode
ERROR_CODE_INVALID_ARGUMENT: ErrorCode
ERROR_CODE_NOT_FOUND: ErrorCode
ERROR_CODE_ALREADY_EXISTS: ErrorCode
ERROR_CODE_PERMISSION_DENIED: ErrorCode
ERROR_CODE_UNAUTHENTICATED: ErrorCode
ERROR_CODE_RESOURCE_EXHAUSTED: ErrorCode
ERROR_CODE_FAILED_PRECONDITION: ErrorCode
ERROR_CODE_ABORTED: ErrorCode
ERROR_CODE_OUT_OF_RANGE: ErrorCode
ERROR_CODE_UNIMPLEMENTED: ErrorCode
ERROR_CODE_UNAVAILABLE: ErrorCode
ERROR_CODE_DEADLINE_EXCEEDED: ErrorCode
ERROR_CODE_SCENARIO_NOT_FOUND: ErrorCode
ERROR_CODE_ITEM_NOT_FOUND: ErrorCode
ERROR_CODE_EXPERIMENT_NOT_FOUND: ErrorCode
ERROR_CODE_MODEL_NOT_FOUND: ErrorCode
ERROR_CODE_INVALID_SCENARIO_CONFIG: ErrorCode
ERROR_CODE_RECALL_FAILED: ErrorCode
ERROR_CODE_RANK_FAILED: ErrorCode
ERROR_CODE_RERANK_FAILED: ErrorCode

class ErrorDetail(_message.Message):
    __slots__ = ("code", "message", "field", "detail")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FIELD_FIELD_NUMBER: _ClassVar[int]
    DETAIL_FIELD_NUMBER: _ClassVar[int]
    code: ErrorCode
    message: str
    field: str
    detail: str
    def __init__(self, code: _Optional[_Union[ErrorCode, str]] = ..., message: _Optional[str] = ..., field: _Optional[str] = ..., detail: _Optional[str] = ...) -> None: ...
