from typing import Optional
from telegram import Bot
from telegram.error import TelegramError
from src.tools.templates.tool_template import BaseTool

class TelegramBaseTool(BaseTool):
    """Base class for all Telegram-related tools"""
    
    def __init__(self):
        super().__init__()
        self.bot: Optional[Bot] = None
        
    async def initialize(self, token: str):
        """Initialize the Telegram bot with the given token"""
        self.bot = Bot(token=token)
        
    async def ensure_initialized(self, token: str):
        """Ensure the bot is initialized with the given token"""
        if not self.bot:
            await self.initialize(token)
            
    def format_error(self, error: Exception) -> str:
        """Format error message based on exception type"""
        if isinstance(error, TelegramError):
            return f"Telegram API error: {str(error)}"
        return f"Unexpected error: {str(error)}"
