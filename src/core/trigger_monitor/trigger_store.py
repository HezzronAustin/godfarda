"""
Storage implementation for trigger events.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from .trigger_base import TriggerEvent


class TriggerStore:
    """Manages storage and retrieval of trigger events."""
    
    def __init__(self):
        self._events: Dict[UUID, TriggerEvent] = {}
        self._lock = asyncio.Lock()
        
    async def store_event(self, event: TriggerEvent) -> None:
        """Store a new trigger event."""
        async with self._lock:
            self._events[event.id] = event
    
    async def get_event(self, event_id: UUID) -> Optional[TriggerEvent]:
        """Retrieve a specific event by ID."""
        return self._events.get(event_id)
    
    async def update_event_status(self, event_id: UUID, status: str) -> None:
        """Update the status of an event."""
        if event := self._events.get(event_id):
            event.status = status
    
    async def get_events_by_type(self, trigger_type: str) -> List[TriggerEvent]:
        """Retrieve all events of a specific type."""
        return [e for e in self._events.values() if e.trigger_type == trigger_type]
    
    async def get_events_by_platform(self, platform: str) -> List[TriggerEvent]:
        """Retrieve all events from a specific platform."""
        return [e for e in self._events.values() if e.platform == platform]
    
    async def get_events_in_timerange(self, start: datetime, end: datetime) -> List[TriggerEvent]:
        """Retrieve all events within a specific time range."""
        return [
            e for e in self._events.values()
            if start <= e.timestamp <= end
        ]
