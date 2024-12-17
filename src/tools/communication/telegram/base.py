from typing import Optional
from telegram import Bot
from telegram.error import TelegramError
from src.tools.templates.tool_template import BaseTool
import asyncio
import logging

logger = logging.getLogger(__name__)

class TelegramBaseTool(BaseTool):
    """Base class for all Telegram-related tools"""
    
    def __init__(self):
        super().__init__()
        self.bot: Optional[Bot] = None
        
    async def initialize(self, token: str):
        """Initialize the Telegram bot with the given token"""
        try:
            self.bot = Bot(token=token)
            # Verify token by getting bot info
            me = await self.bot.get_me()
            logger.info(f"Successfully connected to Telegram as @{me.username}")
            return True
        except TelegramError as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            raise RuntimeError(f"Invalid Telegram token: {e}")
        except Exception as e:
            logger.error(f"Unexpected error initializing Telegram bot: {e}")
            raise
            
    async def ensure_initialized(self, token: str):
        """Ensure the bot is initialized with the given token"""
        if not self.bot:
            await self.initialize(token)
            
    def format_error(self, error: Exception) -> str:
        """Format error message based on exception type"""
        if isinstance(error, TelegramError):
            return f"Telegram API error: {str(error)}"
        return f"Unexpected error: {str(error)}"

    async def send_typing_action(self, chat_id: int):
        """Send typing action to indicate the bot is composing a message.
        
        Args:
            chat_id (int): The ID of the chat where the typing action should be shown
        """
        if self.bot:
            await self.bot.send_chat_action(chat_id=chat_id, action='typing')
            
    async def send_message_with_typing(self, chat_id: int, text: str, typing_time: float = 2.0):
        """Send a message with typing animation.
        
        Args:
            chat_id (int): The ID of the chat to send the message to
            text (str): The text message to send
            typing_time (float, optional): Duration to show typing animation in seconds. Defaults to 2.0
        
        Returns:
            Message: The sent message object
        """
        if self.bot:
            # Show typing animation
            await self.send_typing_action(chat_id)
            # Simulate typing delay
            await asyncio.sleep(typing_time)
            # Send the actual message
            return await self.bot.send_message(chat_id=chat_id, text=text)
