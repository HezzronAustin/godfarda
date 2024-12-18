from telethon import TelegramClient, events
from typing import Optional, Callable, Awaitable
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class TelegramBot:
    def __init__(self, session_name: str = "godfarda_bot"):
        """Initialize Telegram bot with API credentials from environment variables."""
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not all([self.api_id, self.api_hash, self.bot_token]):
            raise ValueError("Missing Telegram API credentials in environment variables")
        
        self.client = TelegramClient(session_name, int(self.api_id), self.api_hash)
        self.message_handler: Optional[Callable[[events.NewMessage.Event], Awaitable[None]]] = None
        
    async def start(self):
        """Start the Telegram bot."""
        await self.client.start(bot_token=self.bot_token)
        logging.info("Telegram bot started")
        
    async def stop(self):
        """Stop the Telegram bot."""
        await self.client.disconnect()
        logging.info("Telegram bot stopped")
        
    def set_message_handler(self, handler: Callable[[events.NewMessage.Event], Awaitable[None]]):
        """Set the message handler function."""
        self.message_handler = handler
        
        @self.client.on(events.NewMessage)
        async def message_handler(event: events.NewMessage.Event):
            try:
                await self.message_handler(event)
            except Exception as e:
                logging.error(f"Error handling message: {e}")
                await event.reply("Sorry, an error occurred while processing your message.")
                
    async def send_message(self, chat_id: int, message: str):
        """Send a message to a specific chat."""
        await self.client.send_message(chat_id, message)
        
    async def reply_to(self, event: events.NewMessage.Event, message: str):
        """Reply to a specific message."""
        await event.reply(message)
