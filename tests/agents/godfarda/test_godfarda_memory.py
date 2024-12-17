import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from src.agents.godfarda.godfarda_agent import GodFarda, AgentConfig, AgentInfo
from src.agents.memory.memory_store import MemoryStore

@pytest.fixture
def mock_ollama():
    mock = Mock()
    mock.execute = AsyncMock(return_value=Mock(
        success=True,
        data={"message": {"content": "Test response"}}
    ))
    return mock

@pytest.fixture
def mock_memory_store():
    memory = AsyncMock(spec=MemoryStore)
    memory.add_memory = AsyncMock()
    memory.get_relevant_memories = AsyncMock(return_value=[
        Mock(
            content="Previous test message",
            timestamp=datetime(2024, 12, 17, 6, 18, 11).timestamp()
        )
    ])
    memory.update_working_memory = Mock()
    return memory

@pytest.fixture
async def godfarda(mock_ollama, mock_memory_store):
    config = AgentConfig(
        name="test_godfarda",
        description="Test Agent",
        allowed_tools=["ollama_chat"]
    )
    
    with patch('src.agents.godfarda.godfarda_agent.MemoryStore', return_value=mock_memory_store):
        agent = GodFarda(config)
        agent.tools = {"ollama_chat": mock_ollama}
        return agent

@pytest.mark.asyncio
async def test_memory_initialization(godfarda, mock_memory_store):
    """Test that memory is properly initialized during agent startup"""
    success = await godfarda.initialize()
    assert success is True
    
    await mock_memory_store.add_memory.assert_awaited_once_with(
        "Godfarda initialization",
        "system",
        {"event": "initialization"},
        importance=1.0
    )

@pytest.mark.asyncio
async def test_message_processing_with_memory(godfarda, mock_memory_store):
    """Test that messages are properly stored and context is retrieved"""
    input_data = {
        "message": "Hello Godfarda",
        "user_info": {
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User"
        },
        "platform": "test"
    }
    
    await godfarda.initialize()
    response = await godfarda.process(input_data)
    
    # Verify message was stored
    await mock_memory_store.add_memory.assert_awaited_with(
        "User message: Hello Godfarda",
        "conversation",
        {
            "user": input_data["user_info"],
            "platform": "test",
            "type": "incoming"
        }
    )
    
    # Verify relevant memories were retrieved
    await mock_memory_store.get_relevant_memories.assert_awaited_once_with("Hello Godfarda")
    
    # Verify working memory was updated
    mock_memory_store.update_working_memory.assert_any_call("current_user", input_data["user_info"])
    mock_memory_store.update_working_memory.assert_any_call("platform", "test")
    
    # Verify response was stored
    await mock_memory_store.add_memory.assert_awaited_with(
        "Godfarda response: Test response",
        "conversation",
        {
            "user": input_data["user_info"],
            "type": "outgoing"
        }
    )
    
    assert response["response"] == "Test response"
    assert response["agent"] == "godfarda"

@pytest.mark.asyncio
async def test_agent_delegation_with_memory(godfarda, mock_memory_store):
    """Test that agent delegation properly includes memory context"""
    # Register a test agent
    godfarda.register_agent(
        "test_agent",
        AgentInfo(
            name="test_agent",
            description="Test Agent",
            capabilities=["testing"],
            tools=["test_tool"]
        )
    )
    
    input_data = {
        "message": "@test_agent run a test",
        "user_info": {
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User"
        },
        "platform": "test"
    }
    
    await godfarda.initialize()
    response = await godfarda.process(input_data)
    
    # Verify agent response was stored with agent info
    await mock_memory_store.add_memory.assert_awaited_with(
        "Agent test_agent response: Test response",
        "conversation",
        {
            "user": input_data["user_info"],
            "agent": "test_agent",
            "type": "outgoing"
        }
    )
    
    assert response["response"] == "Test response"
    assert response["agent"] == "test_agent"

@pytest.mark.asyncio
async def test_memory_formatting(godfarda):
    """Test that memories are properly formatted for context"""
    memories = [
        Mock(
            content="Test memory 1",
            timestamp=datetime(2024, 12, 17, 6, 18, 11).timestamp()
        ),
        Mock(
            content="Test memory 2",
            timestamp=datetime(2024, 12, 17, 6, 18, 11).timestamp()
        )
    ]
    
    formatted = godfarda._format_memories(memories)
    expected = (
        "Previous relevant context:\n"
        "[2024-12-17 06:18:11] Test memory 1\n"
        "[2024-12-17 06:18:11] Test memory 2"
    )
    
    assert formatted == expected

@pytest.mark.asyncio
async def test_empty_memory_formatting(godfarda):
    """Test formatting when no memories are available"""
    formatted = godfarda._format_memories([])
    assert formatted == "No relevant previous context."
