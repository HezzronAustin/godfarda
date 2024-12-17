"""Tests for the base AI model components."""

import pytest
from typing import List, Optional, Dict, Any
from src.tools.ai.base import (
    AIModel,
    AIModelFactory,
    Message,
    MessageRole,
    ModelResponse
)

class MockAIModel(AIModel):
    """Mock AI model for testing."""
    
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.initialized = False
        
    async def initialize(self) -> bool:
        if self.should_fail:
            return False
        self.initialized = True
        return True
        
    async def chat(self,
                  messages: List[Message],
                  temperature: float = 0.7,
                  max_tokens: Optional[int] = None,
                  **kwargs) -> ModelResponse:
        if not self.initialized:
            raise RuntimeError("Model not initialized")
            
        if not messages:
            raise ValueError("Messages cannot be empty")
            
        return ModelResponse(
            content="Mock response",
            model="mock_model",
            usage={"total_tokens": 10},
            raw_response={}
        )
        
    async def cleanup(self) -> None:
        self.initialized = False

@pytest.fixture
def mock_model():
    return MockAIModel()

@pytest.fixture
def failed_model():
    return MockAIModel(should_fail=True)

class TestAIModelFactory:
    """Test the AIModelFactory class."""
    
    def test_register_invalid_model(self):
        """Test registering an invalid model class."""
        class InvalidModel:
            pass
            
        with pytest.raises(ValueError):
            AIModelFactory.register("invalid", InvalidModel)
    
    def test_register_and_create_model(self):
        """Test registering and creating a valid model."""
        AIModelFactory.register("mock", MockAIModel)
        model = AIModelFactory.create("mock")
        assert isinstance(model, MockAIModel)
    
    def test_create_unknown_model(self):
        """Test creating an unknown model type."""
        with pytest.raises(ValueError):
            AIModelFactory.create("unknown_model")
    
    def test_available_models(self):
        """Test getting list of available models."""
        AIModelFactory.register("mock", MockAIModel)
        models = AIModelFactory.available_models()
        assert "mock" in models

class TestMockModel:
    """Test the mock AI model implementation."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_model):
        """Test successful model initialization."""
        success = await mock_model.initialize()
        assert success
        assert mock_model.initialized
    
    @pytest.mark.asyncio
    async def test_failed_initialization(self, failed_model):
        """Test failed model initialization."""
        success = await failed_model.initialize()
        assert not success
        assert not failed_model.initialized
    
    @pytest.mark.asyncio
    async def test_chat_without_initialization(self, mock_model):
        """Test chat without initialization."""
        with pytest.raises(RuntimeError):
            await mock_model.chat([
                Message(role=MessageRole.USER, content="Hello")
            ])
    
    @pytest.mark.asyncio
    async def test_chat_with_empty_messages(self, mock_model):
        """Test chat with empty messages."""
        await mock_model.initialize()
        with pytest.raises(ValueError):
            await mock_model.chat([])
    
    @pytest.mark.asyncio
    async def test_successful_chat(self, mock_model):
        """Test successful chat interaction."""
        await mock_model.initialize()
        response = await mock_model.chat([
            Message(role=MessageRole.USER, content="Hello")
        ])
        
        assert isinstance(response, ModelResponse)
        assert response.content == "Mock response"
        assert response.model == "mock_model"
        assert response.usage["total_tokens"] == 10
    
    @pytest.mark.asyncio
    async def test_cleanup(self, mock_model):
        """Test model cleanup."""
        await mock_model.initialize()
        assert mock_model.initialized
        
        await mock_model.cleanup()
        assert not mock_model.initialized
