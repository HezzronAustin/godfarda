import logging
import asyncio
from telethon import TelegramClient, events
from src.rag.core import RAGSystem
from src.storage.database import init_db
from src.utils.logging_config import setup_logging
from dotenv import load_dotenv
import os
import time

# Configure logging
setup_logging()
logger = logging.getLogger('telegram_bot')

# Load environment variables
load_dotenv()
logger.debug("Loaded environment variables")

# Get Telegram credentials from environment variables
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not all([API_ID, API_HASH, BOT_TOKEN]):
    logger.error("Missing required Telegram credentials in environment variables")
    raise ValueError("Missing required Telegram credentials")

logger.info("Initialized Telegram credentials")

# Initialize database and RAG system
try:
    logger.info("Initializing database and RAG system")
    engine = init_db()
    rag = RAGSystem(engine=engine)
    logger.info("Successfully initialized database and RAG system")
except Exception as e:
    logger.error(f"Failed to initialize database or RAG system: {e}", exc_info=True)
    raise

# Initialize Telegram client
client = TelegramClient('bot', API_ID, API_HASH)
logger.info("Created Telegram client instance")

@client.on(events.NewMessage)
async def handle_message(event):
    start_time = time.time()
    user_id = str(event.sender_id)
    
    try:
        if not event.message.text:
            logger.debug(f"Received empty message from user {user_id}")
            return
            
        message = event.message.text.strip()
        logger.info(f"Received message from user {user_id}: {message[:50]}...")
        
        # If it's not a command, treat it as a regular question
        if not message.startswith('/'):
            logger.debug(f"Processing regular message from user {user_id}")
            response = await rag.ask(message, user_id)
            await event.respond(response)
            logger.info(f"Sent response to user {user_id}, processing time: {time.time() - start_time:.2f}s")
            return
        
        # Handle specific commands
        if message.startswith('/ask '):
            query = message[5:].strip()  # Remove '/ask '
            if not query:
                logger.debug(f"User {user_id} sent empty /ask command")
                await event.respond("Please provide a question after /ask")
                return
                
            logger.debug(f"Processing /ask command from user {user_id}: {query[:50]}...")
            response = await rag.ask(query, user_id)
            await event.respond(response)
            logger.info(f"Sent response to /ask command for user {user_id}, processing time: {time.time() - start_time:.2f}s")
        else:
            logger.debug(f"User {user_id} sent unknown command: {message}")
            await event.respond("I understand the following commands:\n/ask [your question]")
    
    except Exception as e:
        logger.error(f"Error processing message from user {user_id}: {str(e)}", exc_info=True)
        error_message = "Sorry, I encountered an error while processing your message."
        try:
            await event.respond(error_message)
            logger.info(f"Sent error message to user {user_id}")
        except Exception as send_error:
            logger.error(f"Failed to send error message to user {user_id}: {str(send_error)}", exc_info=True)

async def main():
    try:
        logger.info("Starting Telegram client")
        await client.start(bot_token=BOT_TOKEN)
        logger.info("Bot started successfully")
        
        # Run the client until disconnected
        logger.info("Bot is now running")
        await client.run_until_disconnected()
        logger.info("Bot has been disconnected")
        
    except Exception as e:
        logger.error(f"Critical error in main function: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise
