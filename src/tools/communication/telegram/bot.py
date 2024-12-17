"""
Telegram Bot Module

This module initializes and runs the Telegram bot.
"""

import os
import logging
import asyncio
from typing import Optional
from telegram.ext import Application, MessageHandler, filters
from .handler import TelegramHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def setup_bot(token: str, admin_chat_id: Optional[int] = None) -> Application:
    """Set up the Telegram bot.
    
    Args:
        token: Telegram bot token
        admin_chat_id: Optional admin chat ID for restricted access
        
    Returns:
        Configured Application instance
    """
    # Create application
    application = Application.builder().token(token).build()
    
    # Create handler
    handler = TelegramHandler(application.bot, admin_chat_id)
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler.execute))
    
    return application

async def main():
    """Main function to run the bot."""
    try:
        # Get bot token from environment
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
        
        # Get admin chat ID if set
        admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT")
        if admin_chat_id:
            admin_chat_id = int(admin_chat_id)
        
        # Set up and start bot
        application = await setup_bot(token, admin_chat_id)
        await application.initialize()
        await application.start()
        await application.run_polling()
        
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
