from typing import Callable

from pygskin.events import Event


class EventMap(dict[Event, Callable[[], None]]):
    """Add this component to entities that need to track events."""
