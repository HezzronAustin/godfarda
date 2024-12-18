from telethon import TelegramClient, events
from typing import Optional, Callable, Awaitable, List
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import os
from sqlalchemy.orm import Session

from src.telegram.agent_manager import AgentManager
from src.telegram.base import BaseTelegramHandler

# Load environment variables
load_dotenv()

class TelegramBot:
    def __init__(self, session: Session, session_name: str = "godfarda_bot"):
        """Initialize Telegram bot with API credentials from environment variables."""
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not all([self.api_id, self.api_hash, self.bot_token]):
            raise ValueError("Missing Telegram API credentials in environment variables")
        
        self.client = TelegramClient(session_name, int(self.api_id), self.api_hash)
        self.db_session = session
        self.handlers: List[BaseTelegramHandler] = []
        self.message_handler: Optional[Callable[[events.NewMessage.Event], Awaitable[None]]] = None
        self.handled_commands = set()  # Track registered commands
        
        # Initialize handlers
        self._init_handlers()
        
    def _init_handlers(self):
        """Initialize all telegram handlers"""
        # Add AgentManager to handlers
        agent_manager = AgentManager(self.db_session)
        self.handlers.append(agent_manager)
        
        # Register the help command
        @self.client.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            help_text = "Available commands:\n\n"
            help_text += "/help - Show this help message\n"
            help_text += "/ask [question] - Ask a question\n"
            help_text += "/create_agent - Create a new agent\n"
            help_text += "/list_agents - List all available agents\n"
            help_text += "/agent_info [name] - Show detailed info about an agent"
            await event.respond(help_text)
        
    async def start(self):
        """Start the Telegram bot and register all handlers."""
        await self.client.start(bot_token=self.bot_token)
        
        # Register all handlers
        for handler in self.handlers:
            await handler.register_handlers(self.client)
            
        # Register the catch-all handler last
        if self.message_handler:
            @self.client.on(events.NewMessage)
            async def catch_all_handler(event: events.NewMessage.Event):
                # Only handle messages that weren't handled by command handlers
                if not event.pattern_match:
                    try:
                        await self.message_handler(event)
                    except Exception as e:
                        logging.error(f"Error handling message: {e}")
                        await event.reply("Sorry, an error occurred while processing your message.")
            
        logging.info("Telegram bot started with all handlers registered")
        
    async def stop(self):
        """Stop the Telegram bot."""
        await self.client.disconnect()
        logging.info("Telegram bot stopped")
        
    def set_message_handler(self, handler: Callable[[events.NewMessage.Event], Awaitable[None]]):
        """Set the message handler function for non-command messages."""
        self.message_handler = handler
        
    async def send_message(self, chat_id: int, message: str):
        """Send a message to a specific chat."""
        await self.client.send_message(chat_id, message)
        
    async def reply_to(self, event: events.NewMessage.Event, message: str):
        """Reply to a specific message."""
        await event.reply(message)
