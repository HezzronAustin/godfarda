import logging
import asyncio
from sqlalchemy.orm import Session
from src.rag.core import RAGSystem
from src.storage.database import init_db
from src.utils.logging_config import setup_logging
from src.telegram.client import TelegramBot
import time

# Configure logging
setup_logging()
logger = logging.getLogger('telegram_bot')

# Initialize database and RAG system
try:
    logger.info("Initializing database and RAG system")
    engine = init_db()
    session = Session(engine)
    rag = RAGSystem(engine=engine)
    logger.info("Successfully initialized database and RAG system")
except Exception as e:
    logger.error(f"Failed to initialize database or RAG system: {e}", exc_info=True)
    raise

async def handle_message(event):
    """Handle regular messages and /ask commands"""
    start_time = time.time()
    user_id = str(event.sender_id)
    
    try:
        if not event.message.text:
            logger.debug(f"Received empty message from user {user_id}")
            return
            
        message = event.message.text.strip()
        logger.info(f"Received message from user {user_id}: {message[:50]}...")
        
        # Check if user is in an active workflow
        from src.telegram.agent_manager import AgentManager
        if AgentManager.is_user_in_workflow(int(user_id)):
            logger.debug(f"User {user_id} is in a workflow, skipping RAG processing")
            return
        
        # If it's not a command, treat it as a regular question
        if not message.startswith('/'):
            logger.debug(f"Processing regular message from user {user_id}")
            response = await rag.ask(message, user_id)
            await event.respond(response)
            logger.info(f"Sent response to user {user_id}, processing time: {time.time() - start_time:.2f}s")
            return
        
        # Handle /ask command
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
        # Initialize bot with database session
        bot = TelegramBot(session=session)
        
        # Set the message handler for non-command messages
        bot.set_message_handler(handle_message)
        
        # Start the bot
        logger.info("Starting Telegram bot")
        await bot.start()
        logger.info("Bot started successfully")
        
        # Run until disconnected
        logger.info("Bot is now running")
        await bot.client.run_until_disconnected()
        logger.info("Bot has been disconnected")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        raise
    finally:
        await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise
