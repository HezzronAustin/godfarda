import asyncio
import os
import json
import logging
from dotenv import load_dotenv
from src.tools.telegram.message import TelegramMessageTool
from src.tools.telegram.handler import TelegramHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/telegram_ai.log')
    ]
)
logger = logging.getLogger(__name__)

async def main():
    # Load environment variables
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Initialize tools
    message_tool = TelegramMessageTool()
    handler = TelegramHandler()
    
    logger.info("Starting AI Telegram Bot...")
    logger.info("Waiting for messages...")
    
    last_processed_update_id = None
    
    # Main loop to check for and handle messages
    while True:
        try:
            # Get updates with offset to avoid processing old messages
            get_updates_params = {
                "action": "get_updates",
                "token": token
            }
            if last_processed_update_id is not None:
                get_updates_params["offset"] = last_processed_update_id + 1
            
            result = await message_tool.execute(get_updates_params)
            
            if result.success and result.data["updates"]:
                updates = result.data["updates"]
                logger.info(f"Received {len(updates)} new updates")
                
                # Process each update
                for update in updates:
                    update_id = update["update_id"]
                    if update.get("message") and update["message"].get("text"):
                        message_text = update["message"]["text"]
                        chat_id = update["message"]["chat"]["id"]
                        logger.info(f"Processing message: '{message_text}' from chat_id: {chat_id}")
                        
                        # Only process if it's a new message
                        if last_processed_update_id is None or update_id > last_processed_update_id:
                            # Handle the update with AI
                            logger.info("Sending to AI handler...")
                            response = await handler.execute({
                                "action": "handle_update",
                                "token": token,
                                "update": update
                            })
                            logger.info(f"AI handler response: {json.dumps(response.__dict__, indent=2)}")
                            
                            if not response.success:
                                logger.error(f"Error handling update: {response.error}")
                            
                            last_processed_update_id = update_id
                    else:
                        logger.info(f"Skipping non-text message update: {update_id}")
            
            # Small delay to avoid hammering the API
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            await asyncio.sleep(5)  # Longer delay on error

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    asyncio.run(main())
