from __future__ import annotations

import inspect
import typing

import pygame

from pygskin import ecs


def handles_event(event) -> typing.Callable[[typing.Callable], bool]:
    def _handles_event(attr) -> bool:
        if (
            inspect.ismethod(attr)
            and (type_hints := typing.get_type_hints(attr, include_extras=True))
            and (type_hint := list(type_hints.values())[0])
            and typing.get_origin(type_hint) is typing.Annotated
            and type_hint.__origin__ is pygame.event.Event
        ):
            handled_event = pygame.event.Event(*type_hint.__metadata__)
            return (
                handled_event.type == event.type
                and handled_event.__dict__.items() <= event.__dict__.items()
            )

        return False

    return _handles_event


class EventDispatch(ecs.System):
    def update(self, _entities, *args, **kwargs) -> None:
        if "events" not in kwargs:
            kwargs["events"] = list(pygame.event.get())
        for entity in _entities:
            self.update_entity(entity, *args, **kwargs)

    def update_entity(self, entity, *args, **kwargs) -> None:
        for event in kwargs.get("events", []):
            for _, handler in inspect.getmembers(entity, handles_event(event)):
                handler(event)
