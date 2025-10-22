"""
pytest配置文件
"""
import pytest


@pytest.fixture(scope="session")
def event_loop_policy():
    """设置事件循环策略"""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()

