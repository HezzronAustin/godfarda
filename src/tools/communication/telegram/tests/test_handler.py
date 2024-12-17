"""Unit tests for the Telegram handler."""

import pytest
from unittest.mock import MagicMock, patch
from src.tools.communication.telegram.handler import TelegramHandler
from src.tools.communication.telegram.message import TelegramMessageTool
from src.tools.ai.ollama.chat import OllamaChatTool

@pytest.fixture
def mock_ollama():
    tool = MagicMock(spec=OllamaChatTool)
    tool.execute.return_value = {"success": True, "response": "AI Response"}
    return tool

@pytest.fixture
def handler(mock_ollama):
    handler = TelegramHandler()
    handler.ollama = mock_ollama
    return handler

class TestTelegramHandler:
    """Test the TelegramHandler class."""
    
    def test_initialization(self):
        """Test handler initialization."""
        handler = TelegramHandler()
        assert handler is not None
        assert hasattr(handler, 'bot')
        assert hasattr(handler, 'ollama')
    
    @pytest.mark.asyncio
    async def test_handle_update(self, handler):
        """Test handling an update."""
        params = {
            "action": "handle_update",
            "token": "test_token",
            "update": {
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "chat": {"id": "123"},
                    "text": "Hello"
                }
            }
        }
        
        with patch('telegram.Bot') as mock_bot:
            mock_message = MagicMock()
            mock_message.message_id = 2
            mock_bot.return_value.send_message.return_value = mock_message
            
            response = await handler.execute(params)
            assert response.success
            assert response.data["sent_message_id"] == 2
    
    @pytest.mark.asyncio
    async def test_process_update(self, handler):
        """Test processing an update."""
        params = {
            "action": "process_update",
            "update": {
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "chat": {"id": "123"},
                    "text": "Hello"
                }
            }
        }
        
        response = await handler.execute(params)
        assert response.success
        assert response.data["user_id"] == "123"
        assert response.data["message"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_process_invalid_update(self, handler):
        """Test processing an invalid update."""
        params = {
            "action": "process_update",
            "update": {"invalid": "data"}
        }
        
        response = await handler.execute(params)
        assert not response.success
        assert "Invalid update format" in response.error
    
    @pytest.mark.asyncio
    async def test_setup_webhook(self, handler):
        """Test setting up a webhook."""
        params = {
            "action": "setup_webhook",
            "token": "test_token",
            "url": "https://example.com/webhook"
        }
        
        with patch('telegram.Bot') as mock_bot:
            mock_bot.return_value.set_webhook.return_value = True
            
            response = await handler.execute(params)
            assert response.success
    
    @pytest.mark.asyncio
    async def test_setup_webhook_failure(self, handler):
        """Test webhook setup failure."""
        params = {
            "action": "setup_webhook",
            "token": "test_token",
            "url": "invalid-url"
        }
        
        with patch('telegram.Bot') as mock_bot:
            mock_bot.return_value.set_webhook.side_effect = Exception("Invalid URL")
            
            response = await handler.execute(params)
            assert not response.success
            assert "Unexpected error" in response.error
