import logging
import asyncio
from telethon import TelegramClient, events
from src.rag.core import RAGSystem
from src.storage.database import init_db
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Telegram credentials from environment variables
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Initialize database and RAG system
engine = init_db()
rag = RAGSystem(engine=engine)

# Initialize Telegram client
client = TelegramClient('bot', API_ID, API_HASH)

@client.on(events.NewMessage)
async def handle_message(event):
    try:
        if event.message.text:
            user_id = str(event.sender_id)
            message = event.message.text.strip()
            
            # If it's not a command, treat it as a regular question
            if not message.startswith('/'):
                response = await rag.ask(message, user_id)
                await event.respond(response)
                return
            
            # Handle specific commands
            if message.startswith('/ask '):
                query = message[5:].strip()  # Remove '/ask '
                if not query:
                    await event.respond("Please provide a question after /ask")
                    return
                response = await rag.ask(query, user_id)
                await event.respond(response)
            else:
                await event.respond("I understand the following commands:\n/ask [your question]")
    
    except Exception as e:
        logging.error(f"Error processing message: {e}", exc_info=True)
        await event.respond("Sorry, I encountered an error while processing your message.")

async def main():
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start the client
    await client.start(bot_token=BOT_TOKEN)
    logging.info("Bot started successfully")
    
    # Run the client until disconnected
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
