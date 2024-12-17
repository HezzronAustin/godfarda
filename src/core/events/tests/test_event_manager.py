import unittest
from datetime import datetime
from ..event_manager import EventManager, Event
from ..event_types import EventType, EventPlatform, EventCategory

class TestEventManager(unittest.TestCase):
    def setUp(self):
        self.event_manager = EventManager()
        self.test_events = []

    def test_event_triggering(self):
        def handler(event: Event):
            self.test_events.append(event)

        self.event_manager.register_handler(EventType.MESSAGE_RECEIVED, handler)
        
        event = self.event_manager.trigger_event(
            event_type=EventType.MESSAGE_RECEIVED,
            platform=EventPlatform.TELEGRAM,
            category=EventCategory.COMMUNICATION,
            body={"message": "test"}
        )

        self.assertEqual(len(self.test_events), 1)
        self.assertEqual(self.test_events[0].type, EventType.MESSAGE_RECEIVED)
        self.assertEqual(self.test_events[0].body["message"], "test")

    def test_disabled_events(self):
        def handler(event: Event):
            self.test_events.append(event)

        self.event_manager.register_handler(EventType.MESSAGE_RECEIVED, handler)
        self.event_manager.enabled = False
        
        event = self.event_manager.trigger_event(
            event_type=EventType.MESSAGE_RECEIVED,
            platform=EventPlatform.TELEGRAM,
            category=EventCategory.COMMUNICATION,
            body={"message": "test"}
        )

        self.assertEqual(len(self.test_events), 0)
        self.assertIsNone(event)

    def test_get_recent_events(self):
        for i in range(5):
            self.event_manager.trigger_event(
                event_type=EventType.MESSAGE_RECEIVED,
                platform=EventPlatform.TELEGRAM,
                category=EventCategory.COMMUNICATION,
                body={"message": f"test_{i}"}
            )

        recent_events = self.event_manager.get_recent_events(limit=3)
        self.assertEqual(len(recent_events), 3)
        self.assertEqual(recent_events[0].body["message"], "test_4")

if __name__ == '__main__':
    unittest.main()
