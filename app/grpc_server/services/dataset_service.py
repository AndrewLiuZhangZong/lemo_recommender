"""数据集 gRPC 服务实现"""
import grpc
from google.protobuf.json_format import MessageToDict

from recommender.v1 import dataset_pb2, dataset_pb2_grpc
from app.services.dataset import DatasetService
from app.models.dataset import DatasetCreate
from app.models.base import PaginationParams


class DatasetServicer(dataset_pb2_grpc.DatasetServiceServicer):
    """数据集服务 gRPC 实现"""
    
    def __init__(self, db):
        self.service = DatasetService(db)
    
    def _dataset_to_proto(self, dataset) -> dataset_pb2.Dataset:
        """将 Dataset 对象转换为 protobuf 消息"""
        return dataset_pb2.Dataset(
            dataset_id=dataset.dataset_id,
            tenant_id=dataset.tenant_id,
            name=dataset.name,
            description=dataset.description or "",
            storage_type=dataset.storage_type,
            path=dataset.path,
            file_size=dataset.file_size,
            format=dataset.format,
            row_count=dataset.row_count or 0,
            created_by=dataset.created_by,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at or "",
        )
    
    async def CreateDataset(
        self,
        request: dataset_pb2.CreateDatasetRequest,
        context: grpc.aio.ServicerContext
    ) -> dataset_pb2.CreateDatasetResponse:
        """创建数据集"""
        try:
            # 创建数据集
            dataset_data = DatasetCreate(
                tenant_id=request.tenant_id,
                name=request.name,
                description=request.description,
                storage_type=request.storage_type,
                path=request.path,
                file_size=request.file_size,
                format=request.format,
                created_by=request.created_by,
            )
            
            dataset = await self.service.create_dataset(dataset_data)
            
            return dataset_pb2.CreateDatasetResponse(
                dataset=self._dataset_to_proto(dataset)
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to create dataset: {str(e)}")
            return dataset_pb2.CreateDatasetResponse()
    
    async def ListDatasets(
        self,
        request: dataset_pb2.ListDatasetsRequest,
        context: grpc.aio.ServicerContext
    ) -> dataset_pb2.ListDatasetsResponse:
        """获取数据集列表"""
        try:
            pagination = PaginationParams(
                page=request.page if request.page > 0 else 1,
                page_size=request.page_size if request.page_size > 0 else 20
            )
            
            format_filter = request.format if request.format else None
            
            datasets, total = await self.service.list_datasets(
                request.tenant_id,
                pagination,
                format_filter
            )
            
            return dataset_pb2.ListDatasetsResponse(
                items=[self._dataset_to_proto(ds) for ds in datasets],
                total=total
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to list datasets: {str(e)}")
            return dataset_pb2.ListDatasetsResponse()
    
    async def GetDataset(
        self,
        request: dataset_pb2.GetDatasetRequest,
        context: grpc.aio.ServicerContext
    ) -> dataset_pb2.GetDatasetResponse:
        """获取数据集详情"""
        try:
            dataset = await self.service.get_dataset(
                request.tenant_id,
                request.dataset_id
            )
            
            if not dataset:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Dataset not found")
                return dataset_pb2.GetDatasetResponse()
            
            return dataset_pb2.GetDatasetResponse(
                dataset=self._dataset_to_proto(dataset)
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get dataset: {str(e)}")
            return dataset_pb2.GetDatasetResponse()
    
    async def DeleteDataset(
        self,
        request: dataset_pb2.DeleteDatasetRequest,
        context: grpc.aio.ServicerContext
    ) -> dataset_pb2.DeleteDatasetResponse:
        """删除数据集"""
        try:
            success = await self.service.delete_dataset(
                request.tenant_id,
                request.dataset_id
            )
            
            if not success:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Dataset not found")
                return dataset_pb2.DeleteDatasetResponse(success=False)
            
            return dataset_pb2.DeleteDatasetResponse(success=True)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to delete dataset: {str(e)}")
            return dataset_pb2.DeleteDatasetResponse(success=False)

