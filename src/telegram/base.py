from abc import ABC, abstractmethod
from telethon import TelegramClient

class BaseTelegramHandler(ABC):
    """Base class for all Telegram handlers"""
    
    @abstractmethod
    async def register_handlers(self, client: TelegramClient):
        """Register all handlers with the Telegram client
        
        Args:
            client: The Telegram client instance
        """
        pass
