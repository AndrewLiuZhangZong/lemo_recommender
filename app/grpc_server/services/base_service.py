"""gRPC 服务基类"""
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import json

# 添加 grpc_generated 到 Python 路径
grpc_gen_path = Path(__file__).parent.parent.parent / "grpc_generated" / "python"
sys.path.insert(0, str(grpc_gen_path))

from google.protobuf import struct_pb2, timestamp_pb2
from common.v1 import pagination_pb2


class BaseServicer:
    """gRPC 服务基类，提供通用的转换方法"""
    
    def _struct_to_dict(self, struct: struct_pb2.Struct) -> Dict:
        """将 proto Struct 转换为 dict"""
        return json.loads(struct_pb2.Struct.to_json(struct))
    
    def _dict_to_struct(self, data: Dict, struct: struct_pb2.Struct):
        """将 dict 转换为 proto Struct"""
        struct.update(json.loads(json.dumps(data)))
    
    def _datetime_to_timestamp(self, dt: datetime, ts: timestamp_pb2.Timestamp):
        """将 datetime 转换为 proto Timestamp"""
        if dt:
            ts.FromDatetime(dt)
    
    def _set_page_info(self, page_data: Dict, page_info: pagination_pb2.PageInfo):
        """设置分页信息"""
        page_info.page = page_data.get("page", 1)
        page_info.page_size = page_data.get("page_size", 20)
        page_info.total = page_data.get("total", 0)
        page_info.total_pages = page_data.get("total_pages", 0)
        page_info.has_next = page_data.get("has_next", False)
        page_info.has_prev = page_data.get("has_prev", False)

