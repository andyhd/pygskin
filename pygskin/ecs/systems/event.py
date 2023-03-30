from pygskin import ecs
from pygskin.ecs.components.event import EventMap
from pygskin.events import Event
from pygskin.timer import Timer


class EventSystem(ecs.System):
    """
    Handles events, including keyboard events.

    Given an entity with a EventComponent,
    this system calls the on_event callback when an event is received.
    """

    query = ecs.Entity.has(EventMap)

    def update(self, entities: list[ecs.Entity], **kwargs):
        super().update(reversed(entities), events=list(Event.queue), **kwargs)

    def update_entity(self, entity, events=None, **kwargs):
        for event in events:
            if isinstance(event, Timer):
                event.finish()
            else:
                for ev, action in entity.EventMap.items():
                    if ev.match(event):
                        action(event)
