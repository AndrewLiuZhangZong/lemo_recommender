# -*- coding: utf-8 -*-
"""
用户服务 - gRPC实现
职责：用户画像查询、实时特征获取、用户偏好管理
"""
import sys
import os
import asyncio
from datetime import datetime
from typing import Optional, List
from concurrent import futures

import grpc
from motor.motor_asyncio import AsyncIOMotorClient
from google.protobuf import struct_pb2, timestamp_pb2

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.config import settings
from app.core.service_config import ServiceConfig
from app.core.redis_client import get_redis_client
from app.grpc_generated.python.recommender.v1 import user_pb2
from app.grpc_generated.python.recommender.v1 import user_pb2_grpc
from app.grpc_generated.python.recommender_common.v1 import health_pb2


class UserService:
    """用户服务核心逻辑"""
    
    def __init__(self, db, redis_client=None):
        self.db = db
        self.redis_client = redis_client
        self.user_profiles = db.user_profiles
        
        print("[UserService] 初始化完成")
    
    async def get_user_profile(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str
    ) -> Optional[dict]:
        """获取用户画像"""
        try:
            # 先从Redis缓存获取
            if self.redis_client:
                cache_key = f"user_profile:{tenant_id}:{scenario_id}:{user_id}"
                cached = await self.redis_client.get(cache_key)
                if cached:
                    import json
                    return json.loads(cached)
            
            # 从MongoDB查询
            profile = await self.user_profiles.find_one({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "user_id": user_id
            })
            
            if profile:
                # 写入缓存
                if self.redis_client:
                    import json
                    await self.redis_client.setex(
                        cache_key,
                        3600,  # 1小时过期
                        json.dumps(profile, default=str)
                    )
                
                print(f"[UserService] 获取用户画像: {user_id}")
                return profile
            else:
                print(f"[UserService] 用户画像不存在: {user_id}")
                return None
        except Exception as e:
            print(f"[UserService] 获取用户画像失败: {e}")
            return None
    
    async def batch_get_user_profiles(
        self,
        tenant_id: str,
        scenario_id: str,
        user_ids: List[str]
    ) -> List[dict]:
        """批量获取用户画像"""
        try:
            cursor = self.user_profiles.find({
                "tenant_id": tenant_id,
                "scenario_id": scenario_id,
                "user_id": {"$in": user_ids}
            })
            profiles = await cursor.to_list(length=len(user_ids))
            print(f"[UserService] 批量获取用户画像: {len(profiles)}个")
            return profiles
        except Exception as e:
            print(f"[UserService] 批量获取用户画像失败: {e}")
            return []
    
    async def update_user_profile(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str,
        features: dict
    ) -> Optional[dict]:
        """更新用户画像"""
        try:
            # 更新MongoDB
            result = await self.user_profiles.find_one_and_update(
                {
                    "tenant_id": tenant_id,
                    "scenario_id": scenario_id,
                    "user_id": user_id
                },
                {
                    "$set": {
                        **features,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True,
                return_document=True
            )
            
            # 删除缓存
            if self.redis_client:
                cache_key = f"user_profile:{tenant_id}:{scenario_id}:{user_id}"
                await self.redis_client.delete(cache_key)
            
            print(f"[UserService] 更新用户画像: {user_id}")
            return result
        except Exception as e:
            print(f"[UserService] 更新用户画像失败: {e}")
            return None
    
    async def get_user_realtime_features(
        self,
        tenant_id: str,
        scenario_id: str,
        user_id: str
    ) -> Optional[dict]:
        """获取用户实时特征（从Redis）"""
        if not self.redis_client:
            return None
        
        try:
            # 从Redis获取实时特征
            cache_key = f"user_realtime:{tenant_id}:{scenario_id}:{user_id}"
            cached = await self.redis_client.get(cache_key)
            if cached:
                import json
                features = json.loads(cached)
                print(f"[UserService] 获取实时特征: {user_id}")
                return features
            else:
                print(f"[UserService] 实时特征不存在: {user_id}")
                return None
        except Exception as e:
            print(f"[UserService] 获取实时特征失败: {e}")
            return None


def _convert_profile_to_pb(profile: dict) -> user_pb2.UserProfile:
    """转换用户画像为protobuf消息"""
    pb_profile = user_pb2.UserProfile(
        id=str(profile.get("_id", "")),
        tenant_id=profile.get("tenant_id", ""),
        scenario_id=profile.get("scenario_id", ""),
        user_id=profile.get("user_id", ""),
        view_count=profile.get("view_count", 0),
        like_count=profile.get("like_count", 0),
        favorite_count=profile.get("favorite_count", 0),
        share_count=profile.get("share_count", 0),
        preferred_tags=profile.get("preferred_tags", []),
        preferred_categories=profile.get("preferred_categories", []),
        disliked_tags=profile.get("disliked_tags", []),
        active_hours=profile.get("active_hours", []),
        active_weekdays=profile.get("active_weekdays", [])
    )
    
    # 设置额外特征
    if "features" in profile:
        pb_profile.features.update(profile["features"])
    
    # 设置时间戳
    if "created_at" in profile:
        ts = timestamp_pb2.Timestamp()
        ts.FromDatetime(profile["created_at"])
        pb_profile.created_at.CopyFrom(ts)
    
    if "updated_at" in profile:
        ts = timestamp_pb2.Timestamp()
        ts.FromDatetime(profile["updated_at"])
        pb_profile.updated_at.CopyFrom(ts)
    
    return pb_profile


class UserServicer(user_pb2_grpc.UserServiceServicer):
    """用户服务gRPC实现"""
    
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    async def GetUserProfile(self, request, context):
        """获取用户画像"""
        try:
            profile = await self.user_service.get_user_profile(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                user_id=request.user_id
            )
            
            if profile:
                return user_pb2.GetUserProfileResponse(
                    profile=_convert_profile_to_pb(profile)
                )
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("User profile not found")
                return user_pb2.GetUserProfileResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get user profile: {str(e)}")
            return user_pb2.GetUserProfileResponse()
    
    async def BatchGetUserProfiles(self, request, context):
        """批量获取用户画像"""
        try:
            profiles = await self.user_service.batch_get_user_profiles(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                user_ids=list(request.user_ids)
            )
            
            pb_profiles = [_convert_profile_to_pb(p) for p in profiles]
            
            return user_pb2.BatchGetUserProfilesResponse(
                profiles=pb_profiles
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to batch get user profiles: {str(e)}")
            return user_pb2.BatchGetUserProfilesResponse()
    
    async def UpdateUserProfile(self, request, context):
        """更新用户画像"""
        try:
            features = dict(request.features) if request.features else {}
            
            profile = await self.user_service.update_user_profile(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                user_id=request.user_id,
                features=features
            )
            
            if profile:
                return user_pb2.UpdateUserProfileResponse(
                    profile=_convert_profile_to_pb(profile)
                )
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Failed to update user profile")
                return user_pb2.UpdateUserProfileResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to update user profile: {str(e)}")
            return user_pb2.UpdateUserProfileResponse()
    
    async def GetUserRealtimeFeatures(self, request, context):
        """获取用户实时特征"""
        try:
            features = await self.user_service.get_user_realtime_features(
                tenant_id=request.tenant_id,
                scenario_id=request.scenario_id,
                user_id=request.user_id
            )
            
            if features:
                pb_features = user_pb2.UserRealtimeFeatures(
                    user_id=features.get("user_id", ""),
                    recent_view_count=features.get("recent_view_count", 0),
                    recent_viewed_items=features.get("recent_viewed_items", []),
                    recent_liked_items=features.get("recent_liked_items", []),
                    timestamp=features.get("timestamp", 0)
                )
                
                if "realtime_features" in features:
                    pb_features.realtime_features.update(features["realtime_features"])
                
                return user_pb2.GetUserRealtimeFeaturesResponse(
                    features=pb_features
                )
            else:
                return user_pb2.GetUserRealtimeFeaturesResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get realtime features: {str(e)}")
            return user_pb2.GetUserRealtimeFeaturesResponse()
    
    async def HealthCheck(self, request, context):
        """健康检查"""
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.SERVING
        )


async def serve():
    """启动gRPC服务"""
    # 从ConfigMap获取配置
    config = ServiceConfig()
    host = os.getenv("GRPC_HOST", "0.0.0.0")
    port = int(os.getenv("GRPC_PORT", "8084"))
    
    # 连接数据库
    mongo_url = config.get_mongodb_url()
    mongo_client = AsyncIOMotorClient(mongo_url)
    db = mongo_client[config.mongodb_database]
    
    # 连接Redis（可选）
    redis_client = None
    try:
        redis_client = await get_redis_client()
    except Exception as e:
        print(f"[UserService] Redis连接失败（继续运行）: {e}")
    
    # 初始化用户服务
    user_service = UserService(db, redis_client)
    
    # 创建gRPC服务器
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )
    
    # 注册服务
    user_pb2_grpc.add_UserServiceServicer_to_server(
        UserServicer(user_service),
        server
    )
    
    # 启动服务器
    server.add_insecure_port(f"{host}:{port}")
    await server.start()
    
    print(f"[UserService] gRPC服务启动于 {host}:{port}")
    print(f"[UserService] MongoDB: {config.mongodb_host}")
    print(f"[UserService] Redis: {'已连接' if redis_client else '未连接'}")
    
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
