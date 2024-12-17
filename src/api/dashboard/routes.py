"""
FastAPI routes for the monitoring dashboard.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from datetime import datetime, timedelta
import asyncio

from src.core.trigger_monitor.trigger_monitor import get_trigger_monitor
from src.core.trigger_monitor.trigger_base import TriggerEvent
from src.core.events import EventManager, EventType, EventPlatform, EventCategory

router = APIRouter()
trigger_monitor = get_trigger_monitor()
event_manager = EventManager()

@router.get("/system-events")
async def get_system_events(
    event_type: str = None,
    platform: str = None,
    category: str = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get system events with optional filtering."""
    try:
        events = []
        if event_type:
            try:
                event_type_enum = EventType[event_type]
                events = event_manager.get_events_by_type(event_type_enum, limit)
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
        else:
            events = event_manager.get_recent_events(limit)

        # Filter by platform if specified
        if platform:
            try:
                platform_enum = EventPlatform[platform]
                events = [e for e in events if e.platform == platform_enum]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")

        # Filter by category if specified
        if category:
            try:
                category_enum = EventCategory[category]
                events = [e for e in events if e.category == category_enum]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

        # Convert events to dict for JSON response
        return [
            {
                "id": e.id,
                "type": e.type.name,
                "platform": e.platform.name,
                "category": e.category.name,
                "timestamp": e.timestamp.isoformat(),
                "body": e.body,
                "response": e.response,
                "metadata": e.metadata
            }
            for e in events
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/event-types")
async def get_event_types() -> Dict[str, List[str]]:
    """Get available event types, platforms, and categories."""
    return {
        "types": [e.name for e in EventType],
        "platforms": [p.name for p in EventPlatform],
        "categories": [c.name for c in EventCategory]
    }

@router.get("/events")
async def get_events(
    event_type: str = None,
    platform: str = None,
    status: str = None,
    last_minutes: int = 60
) -> List[Dict[str, Any]]:
    """Get filtered trigger events."""
    try:
        # Get events by type if specified
        if event_type:
            events = await trigger_monitor.get_events_by_type(event_type)
        elif platform:
            events = await trigger_monitor.get_events_by_platform(platform)
        else:
            # Get all events from store
            events = list(trigger_monitor._store._events.values())

        # Filter by status if specified
        if status:
            events = [e for e in events if e.status == status]

        # Filter by time
        cutoff_time = datetime.utcnow() - timedelta(minutes=last_minutes)
        events = [e for e in events if e.timestamp >= cutoff_time]

        # Convert events to dict for JSON response
        return [
            {
                "id": str(e.id),
                "trigger_type": e.trigger_type,
                "platform": e.platform,
                "timestamp": e.timestamp.isoformat(),
                "content": e.content,
                "metadata": e.metadata,
                "status": e.status
            }
            for e in events
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Get overall statistics about trigger events and system events."""
    try:
        # Get trigger monitor stats
        trigger_events = list(trigger_monitor._store._events.values())
        total_triggers = len(trigger_events)
        
        # Get system event stats
        system_events = event_manager.get_recent_events(1000)  # Get last 1000 events for stats
        events_by_type = {}
        events_by_platform = {}
        events_by_category = {}
        
        for event in system_events:
            # Count by type
            event_type = event.type.name
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
            
            # Count by platform
            platform = event.platform.name
            events_by_platform[platform] = events_by_platform.get(platform, 0) + 1
            
            # Count by category
            category = event.category.name
            events_by_category[category] = events_by_category.get(category, 0) + 1

        return {
            "trigger_events": {
                "total": total_triggers,
                "by_type": {},  # Add trigger event type stats if needed
                "by_platform": {},  # Add trigger platform stats if needed
            },
            "system_events": {
                "total": len(system_events),
                "by_type": events_by_type,
                "by_platform": events_by_platform,
                "by_category": events_by_category
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
