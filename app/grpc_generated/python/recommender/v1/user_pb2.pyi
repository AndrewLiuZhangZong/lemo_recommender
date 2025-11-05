from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from recommender_common.v1 import pagination_pb2 as _pagination_pb2
from recommender_common.v1 import health_pb2 as _health_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class UserProfile(_message.Message):
    __slots__ = ("id", "tenant_id", "scenario_id", "user_id", "view_count", "like_count", "favorite_count", "share_count", "preferred_tags", "preferred_categories", "disliked_tags", "active_hours", "active_weekdays", "features", "created_at", "updated_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    VIEW_COUNT_FIELD_NUMBER: _ClassVar[int]
    LIKE_COUNT_FIELD_NUMBER: _ClassVar[int]
    FAVORITE_COUNT_FIELD_NUMBER: _ClassVar[int]
    SHARE_COUNT_FIELD_NUMBER: _ClassVar[int]
    PREFERRED_TAGS_FIELD_NUMBER: _ClassVar[int]
    PREFERRED_CATEGORIES_FIELD_NUMBER: _ClassVar[int]
    DISLIKED_TAGS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_HOURS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_WEEKDAYS_FIELD_NUMBER: _ClassVar[int]
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    tenant_id: str
    scenario_id: str
    user_id: str
    view_count: int
    like_count: int
    favorite_count: int
    share_count: int
    preferred_tags: _containers.RepeatedScalarFieldContainer[str]
    preferred_categories: _containers.RepeatedScalarFieldContainer[str]
    disliked_tags: _containers.RepeatedScalarFieldContainer[str]
    active_hours: _containers.RepeatedScalarFieldContainer[int]
    active_weekdays: _containers.RepeatedScalarFieldContainer[int]
    features: _struct_pb2.Struct
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., user_id: _Optional[str] = ..., view_count: _Optional[int] = ..., like_count: _Optional[int] = ..., favorite_count: _Optional[int] = ..., share_count: _Optional[int] = ..., preferred_tags: _Optional[_Iterable[str]] = ..., preferred_categories: _Optional[_Iterable[str]] = ..., disliked_tags: _Optional[_Iterable[str]] = ..., active_hours: _Optional[_Iterable[int]] = ..., active_weekdays: _Optional[_Iterable[int]] = ..., features: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class UserRealtimeFeatures(_message.Message):
    __slots__ = ("user_id", "recent_view_count", "recent_viewed_items", "recent_liked_items", "realtime_features", "timestamp")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    RECENT_VIEW_COUNT_FIELD_NUMBER: _ClassVar[int]
    RECENT_VIEWED_ITEMS_FIELD_NUMBER: _ClassVar[int]
    RECENT_LIKED_ITEMS_FIELD_NUMBER: _ClassVar[int]
    REALTIME_FEATURES_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    recent_view_count: int
    recent_viewed_items: _containers.RepeatedScalarFieldContainer[str]
    recent_liked_items: _containers.RepeatedScalarFieldContainer[str]
    realtime_features: _struct_pb2.Struct
    timestamp: int
    def __init__(self, user_id: _Optional[str] = ..., recent_view_count: _Optional[int] = ..., recent_viewed_items: _Optional[_Iterable[str]] = ..., recent_liked_items: _Optional[_Iterable[str]] = ..., realtime_features: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., timestamp: _Optional[int] = ...) -> None: ...

class GetUserProfileRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "user_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    user_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., user_id: _Optional[str] = ...) -> None: ...

class GetUserProfileResponse(_message.Message):
    __slots__ = ("profile",)
    PROFILE_FIELD_NUMBER: _ClassVar[int]
    profile: UserProfile
    def __init__(self, profile: _Optional[_Union[UserProfile, _Mapping]] = ...) -> None: ...

class BatchGetUserProfilesRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "user_ids")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    USER_IDS_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    user_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., user_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class BatchGetUserProfilesResponse(_message.Message):
    __slots__ = ("profiles",)
    PROFILES_FIELD_NUMBER: _ClassVar[int]
    profiles: _containers.RepeatedCompositeFieldContainer[UserProfile]
    def __init__(self, profiles: _Optional[_Iterable[_Union[UserProfile, _Mapping]]] = ...) -> None: ...

class UpdateUserProfileRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "user_id", "features")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    user_id: str
    features: _struct_pb2.Struct
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., user_id: _Optional[str] = ..., features: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class UpdateUserProfileResponse(_message.Message):
    __slots__ = ("profile",)
    PROFILE_FIELD_NUMBER: _ClassVar[int]
    profile: UserProfile
    def __init__(self, profile: _Optional[_Union[UserProfile, _Mapping]] = ...) -> None: ...

class GetUserRealtimeFeaturesRequest(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "user_id")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    user_id: str
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., user_id: _Optional[str] = ...) -> None: ...

class GetUserRealtimeFeaturesResponse(_message.Message):
    __slots__ = ("features",)
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    features: UserRealtimeFeatures
    def __init__(self, features: _Optional[_Union[UserRealtimeFeatures, _Mapping]] = ...) -> None: ...
