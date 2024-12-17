"""
Base classes for the trigger monitoring system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass
class TriggerEvent:
    """Represents a single trigger event in the system."""
    
    id: UUID
    trigger_type: str  # e.g., 'telegram_message', 'webhook', etc.
    platform: str      # e.g., 'telegram', 'slack', etc.
    timestamp: datetime
    content: Dict[str, Any]  # Flexible content storage
    metadata: Optional[Dict[str, Any]] = None
    status: str = 'pending'  # pending, processing, completed, failed
    
    @classmethod
    def create(cls, trigger_type: str, platform: str, content: Dict[str, Any], 
              metadata: Optional[Dict[str, Any]] = None) -> 'TriggerEvent':
        """Factory method to create a new trigger event."""
        return cls(
            id=uuid4(),
            trigger_type=trigger_type,
            platform=platform,
            timestamp=datetime.utcnow(),
            content=content,
            metadata=metadata or {}
        )


class BaseTrigger(ABC):
    """Base class for all trigger types."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def process_event(self, event: TriggerEvent) -> None:
        """Process a trigger event."""
        pass
    
    @abstractmethod
    async def validate_event(self, event: TriggerEvent) -> bool:
        """Validate if the event is properly formatted for this trigger type."""
        pass
    
    def create_event(self, platform: str, content: Dict[str, Any], 
                    metadata: Optional[Dict[str, Any]] = None) -> TriggerEvent:
        """Create a new trigger event for this trigger type."""
        return TriggerEvent.create(
            trigger_type=self.name,
            platform=platform,
            content=content,
            metadata=metadata
        )
