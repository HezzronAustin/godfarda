import logging
import asyncio
from sqlalchemy.orm import Session
from src.telegram.agent_manager import AgentManager
from src.utils.logging_config import setup_logging
from src.telegram.client import TelegramBot
from src.core.ConversationSystem import ConversationSystem
from src.storage.database import init_db, User, session_scope
import time

# Configure logging
setup_logging()
logger = logging.getLogger('telegram_bot')

# Initialize database and conversation system
try:
    logger.info("Initializing database and conversation system")
    engine = init_db()
    conversation_system = ConversationSystem(engine=engine)
    logger.info("Successfully initialized database and conversation system")
except Exception as e:
    logger.error(f"Failed to initialize database or conversation system: {e}", exc_info=True)
    raise


async def handle_message(event):
    """Handle incoming messages"""
    start_time = time.time()
    user_id = str(event.sender_id)

    try:
        # Skip empty messages
        if not event.message.text:
            logger.debug(f"Received empty message from user {user_id}")
            return

        message = event.message.text.strip()
        logger.info(f"Received message from user {user_id}: {message[:50]}...")

        # Check if user is in an agent management workflow
        if AgentManager.is_user_in_workflow(int(user_id)):
            logger.debug(f"User {user_id} is in agent management workflow, skipping conversation processing")
            return

        # Handle commands
        if message.startswith('/'):
            logger.debug(f"Skipping command message: {message[:50]}...")
            return

        # Process message with conversation system
        with session_scope(engine) as session:
            # Get or create user
            user = session.query(User).filter_by(telegram_id=user_id).first()
            if not user:
                user = User(
                    telegram_id=user_id,
                    username=event.sender.username,
                    first_name=event.sender.first_name,
                    last_name=event.sender.last_name
                )
                session.add(user)
                session.commit()

            # Get response from conversation system
            response = await conversation_system.converse(message, user_id=user_id)

            # Send response
            await event.respond(response)

            logger.info(f"Sent response to user {user_id}, processing time: {time.time() - start_time:.2f}s")

    except Exception as e:
        logger.error(f"Error handling message from user {user_id}: {str(e)}", exc_info=True)
        await event.respond("I encountered an error processing your message. Please try again.")


async def main():
    # Initialize bot with database session
    with session_scope(engine) as session:
        bot_manager = TelegramBot(session=session)
        try:
            # Set message handler
            bot_manager.set_message_handler(handle_message)

            # Start bot
            logger.info("Starting Telegram bot")
            await bot_manager.start()
            logger.info("Bot started successfully")

            # Run until disconnected
            logger.info("Bot is now running")
            await bot_manager.client.run_until_disconnected()
            logger.info("Bot has been disconnected")

        except Exception as e:
            logger.error(f"Error in main: {str(e)}", exc_info=True)
            raise
        finally:
            await bot_manager.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise