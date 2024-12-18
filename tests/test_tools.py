import pytest
from src.tools.manager import ToolManager, Tool, ToolPermission

async def dummy_tool(**kwargs):
    return {"result": "success"}

@pytest.fixture
def tool_manager():
    return ToolManager()

@pytest.fixture
def sample_tool():
    return Tool(
        name="test_tool",
        description="A test tool",
        permission=ToolPermission(name="test", description="Test permission", level=1),
        func=dummy_tool
    )

def test_tool_registration(tool_manager, sample_tool):
    tool_manager.register_tool(sample_tool)
    assert "test_tool" in tool_manager.tools
    
def test_duplicate_tool_registration(tool_manager, sample_tool):
    tool_manager.register_tool(sample_tool)
    with pytest.raises(ValueError):
        tool_manager.register_tool(sample_tool)

@pytest.mark.asyncio
async def test_tool_execution(tool_manager, sample_tool):
    tool_manager.register_tool(sample_tool)
    result = await tool_manager.execute_tool(
        "test_tool",
        permissions={"test"},
        context={"test": "value"}
    )
    assert result["result"] == "success"

@pytest.mark.asyncio
async def test_tool_permission_check(tool_manager, sample_tool):
    tool_manager.register_tool(sample_tool)
    with pytest.raises(PermissionError):
        await tool_manager.execute_tool(
            "test_tool",
            permissions={"wrong_permission"},
            context={}
        )

def test_get_available_tools(tool_manager, sample_tool):
    tool_manager.register_tool(sample_tool)
    tools = tool_manager.get_available_tools({"test"})
    assert len(tools) == 1
    assert "test_tool" in tools
    
    # Test with wrong permission
    tools = tool_manager.get_available_tools({"wrong_permission"})
    assert len(tools) == 0
