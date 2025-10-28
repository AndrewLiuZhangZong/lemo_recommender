from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from recommender_common.v1 import pagination_pb2 as _pagination_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Item(_message.Message):
    __slots__ = ("id", "tenant_id", "scenario_id", "item_id", "metadata", "embedding", "status", "created_at", "updated_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    tenant_id: str
    scenario_id: str
    item_id: str
    metadata: _struct_pb2.Struct
    embedding: _containers.RepeatedScalarFieldContainer[float]
    status: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., item_id: _Optional[str] = ..., metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., embedding: _Optional[_Iterable[float]] = ..., status: _Optional[str] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreateItemRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "item_id", "metadata", "embedding")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    item_id: str
    metadata: _struct_pb2.Struct
    embedding: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., item_id: _Optional[str] = ..., metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., embedding: _Optional[_Iterable[float]] = ...) -> None: ...

class CreateItemResponse(_message.Message):
    __slots__ = ("item",)
    ITEM_FIELD_NUMBER: _ClassVar[int]
    item: Item
    def __init__(self, item: _Optional[_Union[Item, _Mapping]] = ...) -> None: ...

class BatchCreateItemsRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "items")
    class ItemInput(_message.Message):
        __slots__ = ("item_id", "metadata", "embedding")
        ITEM_ID_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        EMBEDDING_FIELD_NUMBER: _ClassVar[int]
        item_id: str
        metadata: _struct_pb2.Struct
        embedding: _containers.RepeatedScalarFieldContainer[float]
        def __init__(self, item_id: _Optional[str] = ..., metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., embedding: _Optional[_Iterable[float]] = ...) -> None: ...
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    items: _containers.RepeatedCompositeFieldContainer[BatchCreateItemsRequest.ItemInput]
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., items: _Optional[_Iterable[_Union[BatchCreateItemsRequest.ItemInput, _Mapping]]] = ...) -> None: ...

class BatchCreateItemsResponse(_message.Message):
    __slots__ = ("items", "success_count", "failed_count", "errors")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_COUNT_FIELD_NUMBER: _ClassVar[int]
    FAILED_COUNT_FIELD_NUMBER: _ClassVar[int]
    ERRORS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[Item]
    success_count: int
    failed_count: int
    errors: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ..., success_count: _Optional[int] = ..., failed_count: _Optional[int] = ..., errors: _Optional[_Iterable[str]] = ...) -> None: ...

class GetItemRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "item_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    item_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., item_id: _Optional[str] = ...) -> None: ...

class GetItemResponse(_message.Message):
    __slots__ = ("item",)
    ITEM_FIELD_NUMBER: _ClassVar[int]
    item: Item
    def __init__(self, item: _Optional[_Union[Item, _Mapping]] = ...) -> None: ...

class ListItemsRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "status", "page")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    status: str
    page: _pagination_pb2.PageRequest
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., status: _Optional[str] = ..., page: _Optional[_Union[_pagination_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class ListItemsResponse(_message.Message):
    __slots__ = ("items", "page_info")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_INFO_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[Item]
    page_info: _pagination_pb2.PageInfo
    def __init__(self, items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ..., page_info: _Optional[_Union[_pagination_pb2.PageInfo, _Mapping]] = ...) -> None: ...

class UpdateItemRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "item_id", "metadata", "embedding", "status")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    item_id: str
    metadata: _struct_pb2.Struct
    embedding: _containers.RepeatedScalarFieldContainer[float]
    status: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., item_id: _Optional[str] = ..., metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., embedding: _Optional[_Iterable[float]] = ..., status: _Optional[str] = ...) -> None: ...

class UpdateItemResponse(_message.Message):
    __slots__ = ("item",)
    ITEM_FIELD_NUMBER: _ClassVar[int]
    item: Item
    def __init__(self, item: _Optional[_Union[Item, _Mapping]] = ...) -> None: ...

class DeleteItemRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "item_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    item_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., item_id: _Optional[str] = ...) -> None: ...

class DeleteItemResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class BatchDeleteItemsRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "item_ids")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_IDS_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    item_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., item_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class BatchDeleteItemsResponse(_message.Message):
    __slots__ = ("success_count", "failed_count", "errors")
    SUCCESS_COUNT_FIELD_NUMBER: _ClassVar[int]
    FAILED_COUNT_FIELD_NUMBER: _ClassVar[int]
    ERRORS_FIELD_NUMBER: _ClassVar[int]
    success_count: int
    failed_count: int
    errors: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, success_count: _Optional[int] = ..., failed_count: _Optional[int] = ..., errors: _Optional[_Iterable[str]] = ...) -> None: ...

class SearchItemsRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "query", "filters", "page")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    FILTERS_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    query: str
    filters: _struct_pb2.Struct
    page: _pagination_pb2.PageRequest
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., query: _Optional[str] = ..., filters: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., page: _Optional[_Union[_pagination_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class SearchItemsResponse(_message.Message):
    __slots__ = ("items", "page_info")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    PAGE_INFO_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[Item]
    page_info: _pagination_pb2.PageInfo
    def __init__(self, items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ..., page_info: _Optional[_Union[_pagination_pb2.PageInfo, _Mapping]] = ...) -> None: ...
