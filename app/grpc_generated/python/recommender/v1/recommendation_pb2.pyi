from google.protobuf import struct_pb2 as _struct_pb2
from recommender_common.v1 import health_pb2 as _health_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RecallStrategy(_message.Message):
    __slots__ = ("name", "weight", "limit", "params")
    NAME_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    name: str
    weight: float
    limit: int
    params: _struct_pb2.Struct
    def __init__(self, name: _Optional[str] = ..., weight: _Optional[float] = ..., limit: _Optional[int] = ..., params: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class MultiRecallRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "user_id", "strategies", "filters")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    STRATEGIES_FIELD_NUMBER: _ClassVar[int]
    FILTERS_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    user_id: str
    strategies: _containers.RepeatedCompositeFieldContainer[RecallStrategy]
    filters: _struct_pb2.Struct
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., user_id: _Optional[str] = ..., strategies: _Optional[_Iterable[_Union[RecallStrategy, _Mapping]]] = ..., filters: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class MultiRecallResponse(_message.Message):
    __slots__ = ("item_ids", "count", "debug_info")
    ITEM_IDS_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    DEBUG_INFO_FIELD_NUMBER: _ClassVar[int]
    item_ids: _containers.RepeatedScalarFieldContainer[str]
    count: int
    debug_info: _struct_pb2.Struct
    def __init__(self, item_ids: _Optional[_Iterable[str]] = ..., count: _Optional[int] = ..., debug_info: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class RankRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "user_id", "item_ids", "ranker")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_IDS_FIELD_NUMBER: _ClassVar[int]
    RANKER_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    user_id: str
    item_ids: _containers.RepeatedScalarFieldContainer[str]
    ranker: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., user_id: _Optional[str] = ..., item_ids: _Optional[_Iterable[str]] = ..., ranker: _Optional[str] = ...) -> None: ...

class RankResponse(_message.Message):
    __slots__ = ("ranked_items", "count", "debug_info")
    RANKED_ITEMS_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    DEBUG_INFO_FIELD_NUMBER: _ClassVar[int]
    ranked_items: _containers.RepeatedCompositeFieldContainer[ScoredItem]
    count: int
    debug_info: _struct_pb2.Struct
    def __init__(self, ranked_items: _Optional[_Iterable[_Union[ScoredItem, _Mapping]]] = ..., count: _Optional[int] = ..., debug_info: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class ScoredItem(_message.Message):
    __slots__ = ("item_id", "score")
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    item_id: str
    score: float
    def __init__(self, item_id: _Optional[str] = ..., score: _Optional[float] = ...) -> None: ...

class RerankRule(_message.Message):
    __slots__ = ("name", "params")
    NAME_FIELD_NUMBER: _ClassVar[int]
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    name: str
    params: _struct_pb2.Struct
    def __init__(self, name: _Optional[str] = ..., params: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class RerankRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "user_id", "ranked_items", "rules")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    RANKED_ITEMS_FIELD_NUMBER: _ClassVar[int]
    RULES_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    user_id: str
    ranked_items: _containers.RepeatedCompositeFieldContainer[ScoredItem]
    rules: _containers.RepeatedCompositeFieldContainer[RerankRule]
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., user_id: _Optional[str] = ..., ranked_items: _Optional[_Iterable[_Union[ScoredItem, _Mapping]]] = ..., rules: _Optional[_Iterable[_Union[RerankRule, _Mapping]]] = ...) -> None: ...

class RerankResponse(_message.Message):
    __slots__ = ("reranked_items", "count", "debug_info")
    RERANKED_ITEMS_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    DEBUG_INFO_FIELD_NUMBER: _ClassVar[int]
    reranked_items: _containers.RepeatedCompositeFieldContainer[ScoredItem]
    count: int
    debug_info: _struct_pb2.Struct
    def __init__(self, reranked_items: _Optional[_Iterable[_Union[ScoredItem, _Mapping]]] = ..., count: _Optional[int] = ..., debug_info: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class GetRecommendationsRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "user_id", "count", "filters", "debug")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    FILTERS_FIELD_NUMBER: _ClassVar[int]
    DEBUG_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    user_id: str
    count: int
    filters: _struct_pb2.Struct
    debug: bool
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., user_id: _Optional[str] = ..., count: _Optional[int] = ..., filters: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., debug: bool = ...) -> None: ...

class RecommendedItem(_message.Message):
    __slots__ = ("item_id", "score", "metadata")
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    item_id: str
    score: float
    metadata: _struct_pb2.Struct
    def __init__(self, item_id: _Optional[str] = ..., score: _Optional[float] = ..., metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class GetRecommendationsResponse(_message.Message):
    __slots__ = ("items", "count", "request_id", "debug_info")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    DEBUG_INFO_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[RecommendedItem]
    count: int
    request_id: str
    debug_info: _struct_pb2.Struct
    def __init__(self, items: _Optional[_Iterable[_Union[RecommendedItem, _Mapping]]] = ..., count: _Optional[int] = ..., request_id: _Optional[str] = ..., debug_info: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...
