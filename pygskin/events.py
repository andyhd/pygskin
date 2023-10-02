from __future__ import annotations

import inspect
import sys
import types
import typing
from collections.abc import Callable
from collections.abc import Iterable
from typing import Any

import pygame

from pygskin import ecs
from pygskin.direction import Direction
from pygskin.utils import Decorator


class Event:
    _type: int = -1

    def __init__(self, event: pygame.event.Event) -> None:
        self.metadata = set(event.__dict__.items())
        self.type = event.type
        self.__dict__.update(self.metadata)

    @classmethod
    def build(cls, event: pygame.event.Event) -> Event | None:
        class_name = EVENT_TYPE_MAP.get(event.type)
        if class_name:
            event_class = getattr(sys.modules[__name__], class_name)
            if class_name in ("KeyDown", "KeyUp"):
                subclass_name = KEY_MAP.get(event.key)
                if subclass_name:
                    event_class = getattr(event_class, subclass_name)
            return event_class(event)


KEY_MAP = {
    value: f'{"_" if name[2:].isdigit() else ""}{name[2:].upper()}'
    for name, value in pygame.__dict__.items()
    if name.startswith("K_") and name not in ["K_LAST"]
}

EVENT_TYPE_MAP = {}
for class_name in [
    "KeyDown",
    "KeyUp",
    "MouseButtonDown",
    "MouseButtonUp",
    "MouseMotion",
    "Quit",
]:
    event_type = getattr(pygame, class_name.upper())
    EVENT_TYPE_MAP[event_type] = class_name
    event_class = type(class_name, (Event,), {"_type": event_type})
    setattr(sys.modules[__name__], class_name, event_class)

    if class_name in ("KeyDown", "KeyUp"):
        for value, subclass_name in KEY_MAP.items():
            attrs = {"key": value}
            if subclass_name in ("UP", "DOWN", "LEFT", "RIGHT"):
                attrs["direction"] = Direction[subclass_name]
            setattr(
                event_class,
                subclass_name,
                type(f"{class_name}.{subclass_name}", (event_class,), attrs),
            )


class EventListener(Decorator):
    def __init__(self, *args, **kwargs) -> None:
        self.event_types: set[type] = set()
        super().__init__(*args, **kwargs)

    def add_event_type(self, event_type: type) -> None:
        if isinstance(event_type, types.UnionType | typing._UnionGenericAlias):
            for arg in event_type.__args__:
                self.add_event_type(arg)
        else:
            self.event_types.add(event_type)

    def set_function(self, fn: Callable) -> None:
        super().set_function(fn)

        sig = inspect.signature(fn, eval_str=True)
        for i, (name, param) in enumerate(sig.parameters.items()):
            if i == 0 and name == "self":
                continue
            self.add_event_type(param.annotation)
            break
        else:
            raise ValueError("Event listener must specify an event as first argument")

    def is_listening_for(self, event: Event) -> bool:
        for event_type in self.event_types:
            metadata = set()
            if isinstance(event_type, typing._AnnotatedAlias):
                metadata = set(event_type.__metadata__)
                event_type = event_type.__origin__
            if isinstance(event, event_type) and metadata.issubset(event.metadata):
                return True

    def call_function(self, *args, **kwargs) -> Any:
        match args:
            case (Event() as event,) if self.is_listening_for(event):
                super().call_function(event)

            case ():
                super().call_function(None)


event_listener = EventListener


class EventSystem(ecs.System):
    @classmethod
    def update(cls, entities: Iterable[ecs.Entity], **kwargs) -> None:
        events = list(pygame.event.get())
        for event in events:
            event = Event.build(event)
            for entity in entities:
                cls.update_entity(entity, event=event, **kwargs)

    @classmethod
    def update_entity(cls, entity: ecs.Entity, **kwargs) -> None:
        for attr, value in inspect.getmembers(entity):
            if isinstance(value, EventListener):
                getattr(entity, attr)(kwargs["event"])
