#!/usr/bin/env python3
"""
Milvus初始化脚本
创建向量集合
"""
import asyncio
from app.core.config import settings
from app.core.milvus_client import MilvusClient, MilvusCollections


async def init_milvus_collections():
    """初始化Milvus集合"""
    
    print("=" * 60)
    print("  Milvus向量数据库初始化")
    print("=" * 60)
    print()
    
    if not settings.milvus_enabled:
        print("❌ Milvus未启用（MILVUS_ENABLED=false）")
        print()
        print("启用方法：")
        print("  1. 确认Milvus服务运行: docker ps | grep milvus")
        print("  2. 在.env中设置: MILVUS_ENABLED=true")
        print()
        return
    
    # 创建客户端
    client = MilvusClient(
        host=settings.milvus_host,
        port=settings.milvus_port,
        enabled=True
    )
    
    # 需要创建的集合
    collections = [
        {
            "name": MilvusCollections.items_embeddings("vlog"),
            "dimension": 768,
            "description": "短视频物品向量"
        },
        {
            "name": MilvusCollections.items_embeddings("news"),
            "dimension": 768,
            "description": "新闻物品向量"
        },
        {
            "name": MilvusCollections.user_embeddings("vlog"),
            "dimension": 768,
            "description": "短视频用户向量"
        },
        {
            "name": MilvusCollections.user_embeddings("news"),
            "dimension": 768,
            "description": "新闻用户向量"
        }
    ]
    
    # 创建集合
    print("📦 创建向量集合...")
    print()
    for collection_config in collections:
        success = await client.create_collection(
            collection_name=collection_config["name"],
            dimension=collection_config["dimension"],
            description=collection_config["description"]
        )
        
        if success:
            print(f"  ✅ {collection_config['name']}")
        else:
            print(f"  ❌ {collection_config['name']}")
    
    print()
    print("=" * 60)
    print("  Milvus初始化完成！")
    print("=" * 60)
    print()
    print("📊 已创建集合:")
    for config in collections:
        print(f"  - {config['name']} (dim={config['dimension']})")
    print()
    print("🔍 验证集合:")
    print("  python -c \"from pymilvus import utility; print(utility.list_collections())\"")
    print()
    print("🌐 Attu管理界面:")
    print("  http://localhost:8000")
    print()
    
    # 关闭连接
    client.close()


if __name__ == '__main__':
    asyncio.run(init_milvus_collections())

