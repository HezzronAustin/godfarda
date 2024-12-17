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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'telegram_bot.log'))
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main bot function."""
    try:
        # Initialize tools
        handler = TelegramHandler()
        message_tool = TelegramMessageTool()
        
        # Initialize tools with token
        await handler.initialize(TELEGRAM_BOT_TOKEN)
        await message_tool.initialize(TELEGRAM_BOT_TOKEN)
        
        logger.info("Starting Telegram bot...")
        
        # Keep track of last update ID
        last_update_id = None
        
        # Start receiving updates
        while True:
            try:
                # Get updates from Telegram with offset
                updates_response = await message_tool.execute({
                    "action": "get_updates",
                    "token": TELEGRAM_BOT_TOKEN,
                    "offset": last_update_id + 1 if last_update_id is not None else None
                })
                
                if not updates_response.success:
                    logger.error(f"Failed to get updates: {updates_response.error}")
                    continue
                
                # Process each update
                updates = updates_response.data.get("updates", [])
                for update in updates:
                    if "message" in update and "text" in update["message"]:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        text = message["text"]
                        
                        logger.info(f"Received message from {chat_id}: {text}")
                        
                        # Get AI response
                        response = await handler.execute({
                            "action": "handle_update",
                            "token": TELEGRAM_BOT_TOKEN,
                            "update": {
                                "message": {
                                    "chat": {"id": chat_id},
                                    "text": text
                                }
                            }
                        })
                        
                        if not response.success:
                            error_msg = f"Failed to process message: {response.error}"
                            logger.error(error_msg)
                            # Send error message to user
                            await message_tool.execute({
                                "action": "send_message",
                                "chat_id": chat_id,
                                "text": f"Sorry, I encountered an error: {response.error}",
                                "token": TELEGRAM_BOT_TOKEN
                            })
                    
                    # Update the last processed update ID
                    last_update_id = update["update_id"]
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
            
            # Small delay to avoid hitting rate limits
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    # Create logs directory
    os.makedirs(os.path.join(os.path.dirname(__file__), 'logs'), exist_ok=True)
    
    # Run the bot
    asyncio.run(main())
