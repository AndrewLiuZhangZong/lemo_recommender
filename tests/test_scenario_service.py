"""
场景服务测试
"""
import pytest
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

from app.services.scenario.service import ScenarioService
from app.models.scenario import ScenarioCreate, ScenarioUpdate, ScenarioType, ScenarioConfig


@pytest.fixture
async def db():
    """测试数据库fixture"""
    client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017")
    db = client["lemo_recommender_test"]
    yield db
    # 清理测试数据
    await db.scenarios.delete_many({"tenant_id": "test_tenant"})
    client.close()


@pytest.fixture
def scenario_service(db):
    """场景服务fixture"""
    return ScenarioService(db)


@pytest.mark.asyncio
async def test_create_scenario(scenario_service):
    """测试创建场景"""
    
    data = ScenarioCreate(
        scenario_id="test_vlog",
        scenario_type=ScenarioType.VLOG,
        name="测试短视频场景",
        description="测试用",
        config=ScenarioConfig()
    )
    
    scenario = await scenario_service.create_scenario("test_tenant", data)
    
    assert scenario is not None
    assert scenario.tenant_id == "test_tenant"
    assert scenario.scenario_id == "test_vlog"
    assert scenario.name == "测试短视频场景"


@pytest.mark.asyncio
async def test_get_scenario(scenario_service):
    """测试获取场景"""
    
    # 先创建
    data = ScenarioCreate(
        scenario_id="test_vlog_2",
        scenario_type=ScenarioType.VLOG,
        name="测试场景2",
        config=ScenarioConfig()
    )
    await scenario_service.create_scenario("test_tenant", data)
    
    # 再获取
    scenario = await scenario_service.get_scenario("test_tenant", "test_vlog_2")
    
    assert scenario is not None
    assert scenario.scenario_id == "test_vlog_2"


@pytest.mark.asyncio
async def test_list_scenarios(scenario_service):
    """测试查询场景列表"""
    
    # 创建多个场景
    for i in range(3):
        data = ScenarioCreate(
            scenario_id=f"test_list_{i}",
            scenario_type=ScenarioType.VLOG,
            name=f"测试场景{i}",
            config=ScenarioConfig()
        )
        await scenario_service.create_scenario("test_tenant", data)
    
    # 查询
    scenarios, total = await scenario_service.list_scenarios("test_tenant")
    
    assert total >= 3
    assert len(scenarios) >= 3


@pytest.mark.asyncio
async def test_update_scenario(scenario_service):
    """测试更新场景"""
    
    # 先创建
    data = ScenarioCreate(
        scenario_id="test_update",
        scenario_type=ScenarioType.VLOG,
        name="原始名称",
        config=ScenarioConfig()
    )
    await scenario_service.create_scenario("test_tenant", data)
    
    # 更新
    update_data = ScenarioUpdate(name="更新后的名称")
    updated = await scenario_service.update_scenario("test_tenant", "test_update", update_data)
    
    assert updated is not None
    assert updated.name == "更新后的名称"


@pytest.mark.asyncio
async def test_delete_scenario(scenario_service):
    """测试删除场景"""
    
    # 先创建
    data = ScenarioCreate(
        scenario_id="test_delete",
        scenario_type=ScenarioType.VLOG,
        name="待删除场景",
        config=ScenarioConfig()
    )
    await scenario_service.create_scenario("test_tenant", data)
    
    # 删除
    success = await scenario_service.delete_scenario("test_tenant", "test_delete")
    
    assert success is True
    
    # 确认已删除
    scenario = await scenario_service.get_scenario("test_tenant", "test_delete")
    assert scenario is None

