"""
Telegram Handler Module

This module provides the TelegramHandler class for handling Telegram bot interactions.
"""

import logging
from typing import Any, Dict, Optional
from telegram import Update
from telegram.ext import CallbackContext
from .process_manager import ensure_single_instance
from src.core.langchain.agent import LangChainAgent

logger = logging.getLogger(__name__)

class TelegramHandler:
    """Handler for Telegram bot interactions."""
    
    def __init__(self, bot: Any, admin_chat_id: Optional[int] = None):
        """Initialize the Telegram handler.
        
        Args:
            bot: Telegram bot instance
            admin_chat_id: Optional admin chat ID for restricted access
        """
        self.bot = bot
        self.admin_chat_id = admin_chat_id
        self.agent = LangChainAgent(
            model_name="llama2",
            system_message=(
                "You are GodFarda, a helpful AI assistant. "
                "You can help users with various tasks using your available tools. "
                "Always be respectful and provide clear, concise responses."
            )
        )
    
    async def _is_authorized(self, chat_id: int, user_id: Optional[int]) -> bool:
        """Check if the user is authorized to use the bot.
        
        Args:
            chat_id: Telegram chat ID
            user_id: Optional user ID
            
        Returns:
            True if user is authorized, False otherwise
        """
        if self.admin_chat_id is None:
            return True
        return chat_id == self.admin_chat_id
    
    @ensure_single_instance
    async def execute(self, update: Update, context: CallbackContext) -> None:
        """Execute the Telegram handler."""
        try:
            # Get message information
            message = update.message
            if not message or not message.text:
                return
            
            chat_id = message.chat_id
            user_id = message.from_user.id if message.from_user else None
            username = message.from_user.username if message.from_user else None
            
            # Check if user is authorized
            if not await self._is_authorized(chat_id, user_id):
                await message.reply_text("You are not authorized to use this bot.")
                return
            
            # Process message with LangChain agent
            user_info = {
                "chat_id": chat_id,
                "user_id": user_id,
                "username": username,
                "platform": "telegram"
            }
            
            response = await self.agent.process_message(message.text, user_info)
            
            # Send response
            if response:
                await message.reply_text(response)
            else:
                await message.reply_text("I couldn't process your message. Please try again.")
                
        except Exception as e:
            logger.error(f"Error in Telegram handler: {e}", exc_info=True)
            await message.reply_text("An error occurred while processing your message. Please try again later.")
