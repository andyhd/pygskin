from pygskin.ecs import Entity
from pygskin.ecs import System
from pygskin.ecs.components.event import EventMap
from pygskin.events import Event


class EventSystem(System):
    """
    Handles events, including keyboard events.

    Given an entity with a EventComponent,
    this system calls the on_event callback when an event is received.
    """

    query = Entity.has(EventMap)

    def update(self, entities: list[Entity], **kwargs):
        super().update(entities, events=list(Event.queue), **kwargs)

    def update_entity(self, entity, events=None, **kwargs):
        for event in events:
            for ev, action in entity.EventMap.items():
                if ev.match(event):
                    action(event)
