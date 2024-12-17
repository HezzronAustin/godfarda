from enum import Enum, auto

class EventType(Enum):
    """Types of events that can occur in the system."""
    WEBHOOK_RECEIVED = auto()
    MESSAGE_RECEIVED = auto()
    MESSAGE_CREATED = auto()
    AI_PROMPTED = auto()
    AI_RESPONDED = auto()

class EventPlatform(Enum):
    """Platforms where events can originate."""
    TELEGRAM = auto()
    WEBHOOK = auto()
    DASHBOARD = auto()
    AI_SYSTEM = auto()
    SYSTEM = auto()

class EventCategory(Enum):
    """Categories for grouping related events."""
    COMMUNICATION = auto()
    AI_INTERACTION = auto()
    SYSTEM = auto()
    WEBHOOK = auto()
