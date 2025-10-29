from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Dataset(_message.Message):
    __slots__ = ("dataset_id", "tenant_id", "name", "description", "storage_type", "path", "file_size", "format", "row_count", "created_by", "created_at", "updated_at")
    DATASET_ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    STORAGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    FILE_SIZE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    ROW_COUNT_FIELD_NUMBER: _ClassVar[int]
    CREATED_BY_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    dataset_id: str
    tenant_id: str
    name: str
    description: str
    storage_type: str
    path: str
    file_size: int
    format: str
    row_count: int
    created_by: str
    created_at: str
    updated_at: str
    def __init__(self, dataset_id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., storage_type: _Optional[str] = ..., path: _Optional[str] = ..., file_size: _Optional[int] = ..., format: _Optional[str] = ..., row_count: _Optional[int] = ..., created_by: _Optional[str] = ..., created_at: _Optional[str] = ..., updated_at: _Optional[str] = ...) -> None: ...

class CreateDatasetRequest(_message.Message):
    __slots__ = ("tenant_id", "name", "description", "storage_type", "path", "file_size", "format", "created_by")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    STORAGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    FILE_SIZE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    CREATED_BY_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    name: str
    description: str
    storage_type: str
    path: str
    file_size: int
    format: str
    created_by: str
    def __init__(self, tenant_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., storage_type: _Optional[str] = ..., path: _Optional[str] = ..., file_size: _Optional[int] = ..., format: _Optional[str] = ..., created_by: _Optional[str] = ...) -> None: ...

class CreateDatasetResponse(_message.Message):
    __slots__ = ("dataset",)
    DATASET_FIELD_NUMBER: _ClassVar[int]
    dataset: Dataset
    def __init__(self, dataset: _Optional[_Union[Dataset, _Mapping]] = ...) -> None: ...

class ListDatasetsRequest(_message.Message):
    __slots__ = ("tenant_id", "page", "page_size", "format")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    page: int
    page_size: int
    format: str
    def __init__(self, tenant_id: _Optional[str] = ..., page: _Optional[int] = ..., page_size: _Optional[int] = ..., format: _Optional[str] = ...) -> None: ...

class ListDatasetsResponse(_message.Message):
    __slots__ = ("items", "total")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[Dataset]
    total: int
    def __init__(self, items: _Optional[_Iterable[_Union[Dataset, _Mapping]]] = ..., total: _Optional[int] = ...) -> None: ...

class GetDatasetRequest(_message.Message):
    __slots__ = ("tenant_id", "dataset_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    DATASET_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    dataset_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., dataset_id: _Optional[str] = ...) -> None: ...

class GetDatasetResponse(_message.Message):
    __slots__ = ("dataset",)
    DATASET_FIELD_NUMBER: _ClassVar[int]
    dataset: Dataset
    def __init__(self, dataset: _Optional[_Union[Dataset, _Mapping]] = ...) -> None: ...

class DeleteDatasetRequest(_message.Message):
    __slots__ = ("tenant_id", "dataset_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    DATASET_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    dataset_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., dataset_id: _Optional[str] = ...) -> None: ...

class DeleteDatasetResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...
