"""Event system for Brockston-Studio"""
from typing import Any, Callable, Dict, List

class EventBus:
    """Central event bus for inter-module communication"""
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def emit(self, event_type: str, data: Any = None) -> None:
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Event handler error for {event_type}: {e}")

# Singleton instance
event_bus = EventBus()
