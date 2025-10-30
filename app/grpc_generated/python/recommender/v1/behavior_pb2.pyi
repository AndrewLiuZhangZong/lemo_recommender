from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ActionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ACTION_TYPE_UNSPECIFIED: _ClassVar[ActionType]
    ACTION_TYPE_IMPRESSION: _ClassVar[ActionType]
    ACTION_TYPE_CLICK: _ClassVar[ActionType]
    ACTION_TYPE_VIEW: _ClassVar[ActionType]
    ACTION_TYPE_PLAY: _ClassVar[ActionType]
    ACTION_TYPE_PLAY_END: _ClassVar[ActionType]
    ACTION_TYPE_READ: _ClassVar[ActionType]
    ACTION_TYPE_READ_END: _ClassVar[ActionType]
    ACTION_TYPE_LEARN: _ClassVar[ActionType]
    ACTION_TYPE_COMPLETE: _ClassVar[ActionType]
    ACTION_TYPE_LIKE: _ClassVar[ActionType]
    ACTION_TYPE_DISLIKE: _ClassVar[ActionType]
    ACTION_TYPE_FAVORITE: _ClassVar[ActionType]
    ACTION_TYPE_SHARE: _ClassVar[ActionType]
    ACTION_TYPE_COMMENT: _ClassVar[ActionType]
    ACTION_TYPE_FOLLOW: _ClassVar[ActionType]
    ACTION_TYPE_ADD_CART: _ClassVar[ActionType]
    ACTION_TYPE_ORDER: _ClassVar[ActionType]
    ACTION_TYPE_PAYMENT: _ClassVar[ActionType]
    ACTION_TYPE_PURCHASE: _ClassVar[ActionType]
    ACTION_TYPE_NOT_INTEREST: _ClassVar[ActionType]
    ACTION_TYPE_PAUSE: _ClassVar[ActionType]
    ACTION_TYPE_REPEAT: _ClassVar[ActionType]
    ACTION_TYPE_DOWNLOAD: _ClassVar[ActionType]
    ACTION_TYPE_TRIAL: _ClassVar[ActionType]
    ACTION_TYPE_NOTE: _ClassVar[ActionType]
    ACTION_TYPE_ASK: _ClassVar[ActionType]
    ACTION_TYPE_REVIEW: _ClassVar[ActionType]
    ACTION_TYPE_ADD_PLAYLIST: _ClassVar[ActionType]

class DeviceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEVICE_TYPE_UNSPECIFIED: _ClassVar[DeviceType]
    DEVICE_TYPE_MOBILE: _ClassVar[DeviceType]
    DEVICE_TYPE_PC: _ClassVar[DeviceType]
    DEVICE_TYPE_TABLET: _ClassVar[DeviceType]
    DEVICE_TYPE_TV: _ClassVar[DeviceType]
    DEVICE_TYPE_UNKNOWN: _ClassVar[DeviceType]
ACTION_TYPE_UNSPECIFIED: ActionType
ACTION_TYPE_IMPRESSION: ActionType
ACTION_TYPE_CLICK: ActionType
ACTION_TYPE_VIEW: ActionType
ACTION_TYPE_PLAY: ActionType
ACTION_TYPE_PLAY_END: ActionType
ACTION_TYPE_READ: ActionType
ACTION_TYPE_READ_END: ActionType
ACTION_TYPE_LEARN: ActionType
ACTION_TYPE_COMPLETE: ActionType
ACTION_TYPE_LIKE: ActionType
ACTION_TYPE_DISLIKE: ActionType
ACTION_TYPE_FAVORITE: ActionType
ACTION_TYPE_SHARE: ActionType
ACTION_TYPE_COMMENT: ActionType
ACTION_TYPE_FOLLOW: ActionType
ACTION_TYPE_ADD_CART: ActionType
ACTION_TYPE_ORDER: ActionType
ACTION_TYPE_PAYMENT: ActionType
ACTION_TYPE_PURCHASE: ActionType
ACTION_TYPE_NOT_INTEREST: ActionType
ACTION_TYPE_PAUSE: ActionType
ACTION_TYPE_REPEAT: ActionType
ACTION_TYPE_DOWNLOAD: ActionType
ACTION_TYPE_TRIAL: ActionType
ACTION_TYPE_NOTE: ActionType
ACTION_TYPE_ASK: ActionType
ACTION_TYPE_REVIEW: ActionType
ACTION_TYPE_ADD_PLAYLIST: ActionType
DEVICE_TYPE_UNSPECIFIED: DeviceType
DEVICE_TYPE_MOBILE: DeviceType
DEVICE_TYPE_PC: DeviceType
DEVICE_TYPE_TABLET: DeviceType
DEVICE_TYPE_TV: DeviceType
DEVICE_TYPE_UNKNOWN: DeviceType

class BehaviorContext(_message.Message):
    __slots__ = ("device_type", "os", "location", "ip", "user_agent")
    DEVICE_TYPE_FIELD_NUMBER: _ClassVar[int]
    OS_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    IP_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    device_type: DeviceType
    os: str
    location: str
    ip: str
    user_agent: str
    def __init__(self, device_type: _Optional[_Union[DeviceType, str]] = ..., os: _Optional[str] = ..., location: _Optional[str] = ..., ip: _Optional[str] = ..., user_agent: _Optional[str] = ...) -> None: ...

class VideoScenarioData(_message.Message):
    __slots__ = ("duration", "watch_duration", "completion_rate", "video_quality", "is_fullscreen", "is_muted", "playback_speed", "seek_positions", "buffer_time")
    DURATION_FIELD_NUMBER: _ClassVar[int]
    WATCH_DURATION_FIELD_NUMBER: _ClassVar[int]
    COMPLETION_RATE_FIELD_NUMBER: _ClassVar[int]
    VIDEO_QUALITY_FIELD_NUMBER: _ClassVar[int]
    IS_FULLSCREEN_FIELD_NUMBER: _ClassVar[int]
    IS_MUTED_FIELD_NUMBER: _ClassVar[int]
    PLAYBACK_SPEED_FIELD_NUMBER: _ClassVar[int]
    SEEK_POSITIONS_FIELD_NUMBER: _ClassVar[int]
    BUFFER_TIME_FIELD_NUMBER: _ClassVar[int]
    duration: int
    watch_duration: int
    completion_rate: float
    video_quality: str
    is_fullscreen: bool
    is_muted: bool
    playback_speed: float
    seek_positions: _containers.RepeatedScalarFieldContainer[int]
    buffer_time: int
    def __init__(self, duration: _Optional[int] = ..., watch_duration: _Optional[int] = ..., completion_rate: _Optional[float] = ..., video_quality: _Optional[str] = ..., is_fullscreen: bool = ..., is_muted: bool = ..., playback_speed: _Optional[float] = ..., seek_positions: _Optional[_Iterable[int]] = ..., buffer_time: _Optional[int] = ...) -> None: ...

class EcommerceScenarioData(_message.Message):
    __slots__ = ("price", "currency", "quantity", "discount", "category_path", "brand", "sku_id", "product_tags", "stock_count", "coupon_id")
    PRICE_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    DISCOUNT_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_PATH_FIELD_NUMBER: _ClassVar[int]
    BRAND_FIELD_NUMBER: _ClassVar[int]
    SKU_ID_FIELD_NUMBER: _ClassVar[int]
    PRODUCT_TAGS_FIELD_NUMBER: _ClassVar[int]
    STOCK_COUNT_FIELD_NUMBER: _ClassVar[int]
    COUPON_ID_FIELD_NUMBER: _ClassVar[int]
    price: float
    currency: str
    quantity: int
    discount: float
    category_path: str
    brand: str
    sku_id: str
    product_tags: _containers.RepeatedScalarFieldContainer[str]
    stock_count: int
    coupon_id: str
    def __init__(self, price: _Optional[float] = ..., currency: _Optional[str] = ..., quantity: _Optional[int] = ..., discount: _Optional[float] = ..., category_path: _Optional[str] = ..., brand: _Optional[str] = ..., sku_id: _Optional[str] = ..., product_tags: _Optional[_Iterable[str]] = ..., stock_count: _Optional[int] = ..., coupon_id: _Optional[str] = ...) -> None: ...

class NewsScenarioData(_message.Message):
    __slots__ = ("read_duration", "read_progress", "word_count", "news_type", "source", "author", "keywords", "is_breaking_news", "publish_time")
    READ_DURATION_FIELD_NUMBER: _ClassVar[int]
    READ_PROGRESS_FIELD_NUMBER: _ClassVar[int]
    WORD_COUNT_FIELD_NUMBER: _ClassVar[int]
    NEWS_TYPE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    KEYWORDS_FIELD_NUMBER: _ClassVar[int]
    IS_BREAKING_NEWS_FIELD_NUMBER: _ClassVar[int]
    PUBLISH_TIME_FIELD_NUMBER: _ClassVar[int]
    read_duration: int
    read_progress: float
    word_count: int
    news_type: str
    source: str
    author: str
    keywords: _containers.RepeatedScalarFieldContainer[str]
    is_breaking_news: bool
    publish_time: int
    def __init__(self, read_duration: _Optional[int] = ..., read_progress: _Optional[float] = ..., word_count: _Optional[int] = ..., news_type: _Optional[str] = ..., source: _Optional[str] = ..., author: _Optional[str] = ..., keywords: _Optional[_Iterable[str]] = ..., is_breaking_news: bool = ..., publish_time: _Optional[int] = ...) -> None: ...

class MusicScenarioData(_message.Message):
    __slots__ = ("duration", "play_duration", "artist", "album", "genre", "bpm", "language", "is_vip_only", "audio_quality")
    DURATION_FIELD_NUMBER: _ClassVar[int]
    PLAY_DURATION_FIELD_NUMBER: _ClassVar[int]
    ARTIST_FIELD_NUMBER: _ClassVar[int]
    ALBUM_FIELD_NUMBER: _ClassVar[int]
    GENRE_FIELD_NUMBER: _ClassVar[int]
    BPM_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    IS_VIP_ONLY_FIELD_NUMBER: _ClassVar[int]
    AUDIO_QUALITY_FIELD_NUMBER: _ClassVar[int]
    duration: int
    play_duration: int
    artist: str
    album: str
    genre: str
    bpm: int
    language: str
    is_vip_only: bool
    audio_quality: str
    def __init__(self, duration: _Optional[int] = ..., play_duration: _Optional[int] = ..., artist: _Optional[str] = ..., album: _Optional[str] = ..., genre: _Optional[str] = ..., bpm: _Optional[int] = ..., language: _Optional[str] = ..., is_vip_only: bool = ..., audio_quality: _Optional[str] = ...) -> None: ...

class EducationScenarioData(_message.Message):
    __slots__ = ("course_id", "chapter_id", "lesson_duration", "study_duration", "progress", "exercise_count", "correct_count", "score", "difficulty_level", "is_certificate_course")
    COURSE_ID_FIELD_NUMBER: _ClassVar[int]
    CHAPTER_ID_FIELD_NUMBER: _ClassVar[int]
    LESSON_DURATION_FIELD_NUMBER: _ClassVar[int]
    STUDY_DURATION_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    EXERCISE_COUNT_FIELD_NUMBER: _ClassVar[int]
    CORRECT_COUNT_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    DIFFICULTY_LEVEL_FIELD_NUMBER: _ClassVar[int]
    IS_CERTIFICATE_COURSE_FIELD_NUMBER: _ClassVar[int]
    course_id: str
    chapter_id: str
    lesson_duration: int
    study_duration: int
    progress: float
    exercise_count: int
    correct_count: int
    score: float
    difficulty_level: str
    is_certificate_course: bool
    def __init__(self, course_id: _Optional[str] = ..., chapter_id: _Optional[str] = ..., lesson_duration: _Optional[int] = ..., study_duration: _Optional[int] = ..., progress: _Optional[float] = ..., exercise_count: _Optional[int] = ..., correct_count: _Optional[int] = ..., score: _Optional[float] = ..., difficulty_level: _Optional[str] = ..., is_certificate_course: bool = ...) -> None: ...

class ScenarioSpecificData(_message.Message):
    __slots__ = ("video_data", "ecommerce_data", "news_data", "music_data", "education_data", "custom_data")
    VIDEO_DATA_FIELD_NUMBER: _ClassVar[int]
    ECOMMERCE_DATA_FIELD_NUMBER: _ClassVar[int]
    NEWS_DATA_FIELD_NUMBER: _ClassVar[int]
    MUSIC_DATA_FIELD_NUMBER: _ClassVar[int]
    EDUCATION_DATA_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_DATA_FIELD_NUMBER: _ClassVar[int]
    video_data: VideoScenarioData
    ecommerce_data: EcommerceScenarioData
    news_data: NewsScenarioData
    music_data: MusicScenarioData
    education_data: EducationScenarioData
    custom_data: _struct_pb2.Struct
    def __init__(self, video_data: _Optional[_Union[VideoScenarioData, _Mapping]] = ..., ecommerce_data: _Optional[_Union[EcommerceScenarioData, _Mapping]] = ..., news_data: _Optional[_Union[NewsScenarioData, _Mapping]] = ..., music_data: _Optional[_Union[MusicScenarioData, _Mapping]] = ..., education_data: _Optional[_Union[EducationScenarioData, _Mapping]] = ..., custom_data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class BehaviorEvent(_message.Message):
    __slots__ = ("tenant_id", "scenario_id", "user_id", "item_id", "action_type", "event_id", "timestamp", "context", "experiment_id", "experiment_group", "position", "scenario_data", "extra_data")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    ACTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    EXPERIMENT_GROUP_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    SCENARIO_DATA_FIELD_NUMBER: _ClassVar[int]
    EXTRA_DATA_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    scenario_id: str
    user_id: str
    item_id: str
    action_type: ActionType
    event_id: str
    timestamp: int
    context: BehaviorContext
    experiment_id: str
    experiment_group: str
    position: int
    scenario_data: ScenarioSpecificData
    extra_data: _struct_pb2.Struct
    def __init__(self, tenant_id: _Optional[str] = ..., scenario_id: _Optional[str] = ..., user_id: _Optional[str] = ..., item_id: _Optional[str] = ..., action_type: _Optional[_Union[ActionType, str]] = ..., event_id: _Optional[str] = ..., timestamp: _Optional[int] = ..., context: _Optional[_Union[BehaviorContext, _Mapping]] = ..., experiment_id: _Optional[str] = ..., experiment_group: _Optional[str] = ..., position: _Optional[int] = ..., scenario_data: _Optional[_Union[ScenarioSpecificData, _Mapping]] = ..., extra_data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class TrackEventRequest(_message.Message):
    __slots__ = ("event",)
    EVENT_FIELD_NUMBER: _ClassVar[int]
    event: BehaviorEvent
    def __init__(self, event: _Optional[_Union[BehaviorEvent, _Mapping]] = ...) -> None: ...

class TrackEventResponse(_message.Message):
    __slots__ = ("success", "event_id", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    event_id: str
    message: str
    def __init__(self, success: bool = ..., event_id: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class TrackBatchRequest(_message.Message):
    __slots__ = ("events",)
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[BehaviorEvent]
    def __init__(self, events: _Optional[_Iterable[_Union[BehaviorEvent, _Mapping]]] = ...) -> None: ...

class TrackBatchResponse(_message.Message):
    __slots__ = ("success", "total", "succeeded", "failed", "errors")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    SUCCEEDED_FIELD_NUMBER: _ClassVar[int]
    FAILED_FIELD_NUMBER: _ClassVar[int]
    ERRORS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    total: int
    succeeded: int
    failed: int
    errors: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, success: bool = ..., total: _Optional[int] = ..., succeeded: _Optional[int] = ..., failed: _Optional[int] = ..., errors: _Optional[_Iterable[str]] = ...) -> None: ...

class GetStatsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetStatsResponse(_message.Message):
    __slots__ = ("total_events", "kafka_success", "kafka_failed", "rejected", "success_rate")
    TOTAL_EVENTS_FIELD_NUMBER: _ClassVar[int]
    KAFKA_SUCCESS_FIELD_NUMBER: _ClassVar[int]
    KAFKA_FAILED_FIELD_NUMBER: _ClassVar[int]
    REJECTED_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_RATE_FIELD_NUMBER: _ClassVar[int]
    total_events: int
    kafka_success: int
    kafka_failed: int
    rejected: int
    success_rate: float
    def __init__(self, total_events: _Optional[int] = ..., kafka_success: _Optional[int] = ..., kafka_failed: _Optional[int] = ..., rejected: _Optional[int] = ..., success_rate: _Optional[float] = ...) -> None: ...

class HealthCheckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("status", "kafka_available", "stats")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    KAFKA_AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    STATS_FIELD_NUMBER: _ClassVar[int]
    status: str
    kafka_available: bool
    stats: GetStatsResponse
    def __init__(self, status: _Optional[str] = ..., kafka_available: bool = ..., stats: _Optional[_Union[GetStatsResponse, _Mapping]] = ...) -> None: ...
