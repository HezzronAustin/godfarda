import pytest
from uuid import uuid4
from src.agents.minion import MinionAgent, Task
from src.models.base import ChainableMinion
from src.tools.manager import ToolManager, Tool, ToolPermission

def create_test_tool():
    async def test_func(**kwargs):
        return {"status": "success"}
    
    return Tool(
        name="test_tool",
        description="A test tool",
        permission=ToolPermission(name="test", description="Test permission", level=1),
        func=test_func
    )

@pytest.fixture
def tool_manager():
    manager = ToolManager()
    manager.register_tool(create_test_tool())
    return manager

@pytest.fixture
def root_agent(tool_manager):
    minion = ChainableMinion(
        name="root",
        capabilities={"test"}
    )
    return MinionAgent(minion, tool_manager)

@pytest.mark.asyncio
async def test_agent_task_handling(root_agent):
    task = Task(
        id=uuid4(),
        query="test query",
        context={},
        requires_capabilities={"test"}
    )
    
    result = await root_agent.process_task(task)
    assert result["agent_id"] == root_agent.minion.id
    assert result["task_id"] == task.id

@pytest.mark.asyncio
async def test_agent_delegation(root_agent):
    # Create a child agent with different capabilities
    child_minion = ChainableMinion(
        name="child",
        capabilities={"special"},
        parent_id=root_agent.minion.id
    )
    root_agent.minion.children[child_minion.id] = child_minion
    
    # Create a task requiring special capability
    task = Task(
        id=uuid4(),
        query="special task",
        context={},
        requires_capabilities={"special"}
    )
    
    # Root agent should delegate to child
    child = await root_agent.delegate_task(task)
    assert child is not None
    assert child.capabilities == {"special"}

@pytest.mark.asyncio
async def test_agent_state_management(root_agent):
    task = Task(
        id=uuid4(),
        query="test state",
        context={"test": "value"},
        requires_capabilities={"test"}
    )
    
    await root_agent.process_task(task)
    
    # Verify state was updated
    assert "task" in root_agent.minion.state.context
    assert root_agent.minion.state.context["task"]["query"] == "test state"
