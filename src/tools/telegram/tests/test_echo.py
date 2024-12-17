import asyncio
import os
import logging
from dotenv import load_dotenv
from src.tools.telegram.message import TelegramMessageTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/telegram_echo.log')
    ]
)
logger = logging.getLogger(__name__)

async def main():
    # Load environment variables
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment")
        return
        
    # Initialize tool
    message_tool = TelegramMessageTool()
    
    logger.info("Starting Telegram Echo Bot...")
    last_update_id = None
    
    while True:
        try:
            # Get updates
            params = {
                "action": "get_updates",
                "token": token
            }
            if last_update_id is not None:
                params["offset"] = last_update_id + 1
                
            result = await message_tool.execute(params)
            
            if result.success and result.data["updates"]:
                updates = result.data["updates"]
                logger.info(f"Received {len(updates)} new updates")
                
                for update in updates:
                    update_id = update["update_id"]
                    if update.get("message") and update["message"].get("text"):
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        logger.info(f"Received message: '{text}' from chat {chat_id}")
                        
                        # Echo the message back
                        echo_result = await message_tool.execute({
                            "action": "send_message",
                            "token": token,
                            "chat_id": chat_id,
                            "message": f"You said: {text}"
                        })
                        
                        if echo_result.success:
                            logger.info("Echo sent successfully")
                        else:
                            logger.error(f"Failed to send echo: {echo_result.error}")
                            
                        last_update_id = update_id
                    else:
                        logger.info(f"Skipping non-text message update: {update_id}")
                        last_update_id = update_id
            
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    asyncio.run(main())
