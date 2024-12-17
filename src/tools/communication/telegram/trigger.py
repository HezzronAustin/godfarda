"""
Telegram-specific trigger implementation for the trigger monitoring system.
"""

from typing import Dict, Any, Optional
from src.core.trigger_monitor.trigger_base import BaseTrigger, TriggerEvent


class TelegramTrigger(BaseTrigger):
    """
    Trigger implementation for Telegram messages.
    Tracks and monitors incoming Telegram messages and updates.
    """
    
    def __init__(self):
        super().__init__('telegram_message')
    
    async def validate_event(self, event: TriggerEvent) -> bool:
        """Validate that the event contains required Telegram message data."""
        content = event.content
        return (
            isinstance(content, dict) and
            'update_id' in content and
            ('message' in content or 'callback_query' in content)
        )
    
    async def process_event(self, event: TriggerEvent) -> None:
        """Process the Telegram event - in this case, just update metadata."""
        content = event.content
        event.metadata = event.metadata or {}
        
        if 'message' in content:
            message = content['message']
            event.metadata.update({
                'chat_id': message.get('chat', {}).get('id'),
                'user_id': message.get('from', {}).get('id'),
                'message_type': 'text' if 'text' in message else 'other',
                'message_id': message.get('message_id')
            })
        elif 'callback_query' in content:
            callback = content['callback_query']
            event.metadata.update({
                'chat_id': callback.get('message', {}).get('chat', {}).get('id'),
                'user_id': callback.get('from', {}).get('id'),
                'message_type': 'callback_query',
                'callback_data': callback.get('data')
            })
    
    @classmethod
    def create_from_update(cls, update: Dict[str, Any]) -> TriggerEvent:
        """Create a trigger event from a Telegram update."""
        return TriggerEvent.create(
            trigger_type='telegram_message',
            platform='telegram',
            content=update,
            metadata={}
        )
