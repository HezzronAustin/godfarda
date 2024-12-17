"""Telegram Bot with Ollama Integration.

This script runs a Telegram bot that uses Ollama for AI-powered responses.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from .handler import TelegramHandler
from .message import TelegramMessageTool

# Load environment variables
load_dotenv()

# Get Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'telegram_bot.log')

# Clear existing handlers to avoid duplication
root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)

# Configure file handler with absolute path
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Configure console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Configure root logger
root.setLevel(logging.DEBUG)
root.addHandler(file_handler)
root.addHandler(console_handler)

# Get logger for this module
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized successfully. Log file: {log_file}")

async def main():
    """Main bot function."""
    try:
        # Initialize handler
        handler = TelegramHandler()
        await handler.initialize(TELEGRAM_BOT_TOKEN)
        
        # Delete any existing webhook
        logger.info("Deleting existing webhook...")
        bot = handler.bot
        await bot.delete_webhook()
        logger.info("Webhook deleted successfully")
        
        logger.info("Starting Telegram bot...")
        offset = None
        
        # Start receiving updates
        while True:
            try:
                # Get updates from Telegram with offset
                updates = await bot.get_updates(offset=offset, timeout=30)
                
                for update in updates:
                    # Update offset to mark messages as read
                    offset = update.update_id + 1
                    
                    try:
                        logger.info(f"Processing update: {update.to_dict()}")
                        await handler.process_update(update.to_dict())
                    except Exception as e:
                        logger.error(f"Error processing update: {e}", exc_info=True)
                        # Try to notify user of error
                        try:
                            if update.message:
                                await bot.send_message(
                                    chat_id=update.message.chat_id,
                                    text="Sorry, I encountered an error while processing your message. Please try again."
                                )
                        except Exception as notify_error:
                            logger.error(f"Failed to send error notification: {notify_error}")
                        continue
                        
            except Exception as e:
                logger.error(f"Failed to get updates: {e}", exc_info=True)
                await asyncio.sleep(1)  # Wait before retrying
                
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    # Register tools
    from src.tools import register_tools
    register_tools()
    
    # Check registered tools
    from src.core.registry import registry
    logger.info(f"Registered tools: {registry.list_tools()}")
    
    # Run the bot
    asyncio.run(main())
