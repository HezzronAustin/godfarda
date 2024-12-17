from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import uuid
import logging
from .event_types import EventType, EventPlatform, EventCategory

@dataclass
class Event:
    """Represents a system event."""
    id: str
    type: EventType
    platform: EventPlatform
    category: EventCategory
    timestamp: datetime
    body: Dict[str, Any]
    response: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class EventManager:
    """Manages system-wide events and their handlers."""
    
    def __init__(self):
        self._enabled = True
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._events: List[Event] = []
        self.logger = logging.getLogger(__name__)

    @property
    def enabled(self) -> bool:
        """Get the current enabled state of the event manager."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable event processing."""
        self._enabled = value
        self.logger.info(f"Event manager {'enabled' if value else 'disabled'}")

    def register_handler(self, event_type: EventType, handler: Callable[[Event], None]):
        """Register a handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        self.logger.debug(f"Registered handler for event type: {event_type}")

    def trigger_event(
        self,
        event_type: EventType,
        platform: EventPlatform,
        category: EventCategory,
        body: Dict[str, Any],
        response: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Event]:
        """Trigger a new event and process it through registered handlers."""
        if not self._enabled:
            self.logger.warning("Event manager is disabled. Event not processed.")
            return None

        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            platform=platform,
            category=category,
            timestamp=datetime.utcnow(),
            body=body,
            response=response,
            metadata=metadata
        )
        
        self._events.append(event)
        self._process_event(event)
        return event

    def _process_event(self, event: Event):
        """Process an event through all registered handlers."""
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    self.logger.error(f"Error processing event {event.id}: {str(e)}")

    def get_recent_events(self, limit: int = 100) -> List[Event]:
        """Get the most recent events."""
        return sorted(
            self._events,
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]

    def get_events_by_type(self, event_type: EventType, limit: int = 100) -> List[Event]:
        """Get events filtered by type."""
        return sorted(
            [e for e in self._events if e.type == event_type],
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]

    def clear_events(self):
        """Clear all stored events."""
        self._events.clear()
        self.logger.info("Cleared all events")
