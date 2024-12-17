"""Unit tests for the Telegram message tool."""

import pytest
from unittest.mock import MagicMock, patch
from src.tools.communication.telegram.message import TelegramMessageTool

@pytest.fixture
def message_tool():
    return TelegramMessageTool()

class TestTelegramMessageTool:
    """Test the TelegramMessageTool class."""
    
    def test_initialization(self):
        """Test tool initialization."""
        tool = TelegramMessageTool()
        assert tool is not None
        assert hasattr(tool, 'bot')
    
    @pytest.mark.asyncio
    async def test_send_message(self, message_tool):
        """Test sending a message."""
        params = {
            "action": "send_message",
            "token": "test_token",
            "chat_id": "123",
            "message": "Hello"
        }
        
        with patch('telegram.Bot') as mock_bot:
            mock_message = MagicMock()
            mock_message.message_id = 1
            mock_message.chat.id = 123
            mock_message.date.isoformat.return_value = "2024-01-01T00:00:00"
            mock_bot.return_value.send_message.return_value = mock_message
            
            response = await message_tool.execute(params)
            assert response.success
            assert response.data["message_id"] == 1
            assert response.data["chat_id"] == 123
    
    @pytest.mark.asyncio
    async def test_send_message_failure(self, message_tool):
        """Test message sending failure."""
        params = {
            "action": "send_message",
            "token": "test_token",
            "chat_id": "123",
            "message": ""
        }
        
        response = await message_tool.execute(params)
        assert not response.success
        assert "Message parameter is required" in response.error
    
    @pytest.mark.asyncio
    async def test_get_updates(self, message_tool):
        """Test getting updates."""
        params = {
            "action": "get_updates",
            "token": "test_token"
        }
        
        mock_updates = [
            MagicMock(
                update_id=1,
                message=MagicMock(
                    message_id=1,
                    chat=MagicMock(id=123),
                    text="Hello",
                    date=MagicMock(isoformat=lambda: "2024-01-01T00:00:00")
                )
            )
        ]
        
        with patch('telegram.Bot') as mock_bot:
            mock_bot.return_value.get_updates.return_value = mock_updates
            
            response = await message_tool.execute(params)
            assert response.success
            assert len(response.data["updates"]) == 1
            assert response.data["updates"][0]["update_id"] == 1
    
    @pytest.mark.asyncio
    async def test_get_updates_failure(self, message_tool):
        """Test updates retrieval failure."""
        params = {
            "action": "get_updates",
            "token": "invalid_token"
        }
        
        with patch('telegram.Bot') as mock_bot:
            mock_bot.return_value.get_updates.side_effect = Exception("API Error")
            
            response = await message_tool.execute(params)
            assert not response.success
            assert "Unexpected error" in response.error
    
    @pytest.mark.asyncio
    async def test_get_updates_with_offset(self, message_tool):
        """Test getting updates with offset."""
        params = {
            "action": "get_updates",
            "token": "test_token",
            "offset": 100
        }
        
        with patch('telegram.Bot') as mock_bot:
            mock_bot.return_value.get_updates.return_value = []
            
            response = await message_tool.execute(params)
            assert response.success
            assert response.data["updates"] == []
            mock_bot.return_value.get_updates.assert_called_once_with(offset=100)
