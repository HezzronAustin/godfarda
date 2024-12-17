"""
Main trigger monitoring system implementation.
"""

import asyncio
from typing import Dict, List, Optional, Type
from functools import lru_cache

from .trigger_base import BaseTrigger, TriggerEvent
from .trigger_store import TriggerStore


@lru_cache(maxsize=1)
def get_trigger_monitor() -> 'TriggerMonitor':
    """Get the singleton instance of TriggerMonitor."""
    return TriggerMonitor()


class TriggerMonitor:
    """
    Central system for monitoring and managing triggers.
    Handles registration of trigger types and processing of trigger events.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TriggerMonitor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._triggers: Dict[str, BaseTrigger] = {}
            self._store = TriggerStore()
            self._processing_tasks: Dict[str, asyncio.Task] = {}
            self._initialized = True
    
    def register_trigger(self, trigger: BaseTrigger) -> None:
        """Register a new trigger type."""
        self._triggers[trigger.name] = trigger
    
    async def process_event(self, event: TriggerEvent) -> None:
        """
        Process a trigger event asynchronously.
        This method is non-blocking and returns immediately while processing continues
        in the background.
        """
        if trigger := self._triggers.get(event.trigger_type):
            # Store the event first
            await self._store.store_event(event)
            
            # Create a background task to process the event
            task = asyncio.create_task(self._process_event(trigger, event))
            self._processing_tasks[str(event.id)] = task
            
            # Clean up task when done
            task.add_done_callback(
                lambda t: self._processing_tasks.pop(str(event.id), None)
            )
    
    async def _process_event(self, trigger: BaseTrigger, event: TriggerEvent) -> None:
        """Internal method to process an event with error handling."""
        try:
            # Update status to processing
            await self._store.update_event_status(event.id, 'processing')
            
            # Validate and process the event
            if await trigger.validate_event(event):
                await trigger.process_event(event)
                await self._store.update_event_status(event.id, 'completed')
            else:
                await self._store.update_event_status(event.id, 'failed')
        except Exception as e:
            # Update status to failed on error
            await self._store.update_event_status(event.id, 'failed')
            event.metadata = event.metadata or {}
            event.metadata['error'] = str(e)
    
    async def get_event(self, event_id: str) -> Optional[TriggerEvent]:
        """Retrieve a specific event by ID."""
        return await self._store.get_event(event_id)
    
    async def get_events_by_type(self, trigger_type: str) -> List[TriggerEvent]:
        """Retrieve all events of a specific type."""
        return await self._store.get_events_by_type(trigger_type)
    
    async def get_events_by_platform(self, platform: str) -> List[TriggerEvent]:
        """Retrieve all events from a specific platform."""
        return await self._store.get_events_by_platform(platform)
