from __future__ import annotations

import sys
from inspect import Parameter
from inspect import Signature
from typing import Any
from typing import Type

import pygame

EventClass = type["Event"]


class Event:
    CLASSES: dict[int, EventClass] = {}
    signature: Signature
    type: int

    def __init__(self, *args, **kwargs) -> None:
        params = self.signature.bind(*args, **kwargs)
        params.apply_defaults()
        kwargs = params.arguments.pop("kwargs", {})
        self.__dict__.update(params.arguments)
        self.__dict__.update(kwargs)
        self._ignore = False

    def match(self, other: Any) -> bool:
        return (
            isinstance(other, (Event, pygame.event.Event, pygame.event.EventType))
            and self.type == other.type
            and self.__dict__.items() <= other.__dict__.items()
            and not getattr(other, "_ignore", False)
        )

    def __eq__(self, other: Any) -> bool:
        return self.match(other)

    def __hash__(self):
        return hash((self.type, repr(self.__dict__)))

    def stopPropagation(self) -> None:
        self._ignore = True

    @property
    def event(self) -> pygame.event.Event:
        return pygame.event.Event(self.type, self.__dict__)

    @classmethod
    def build(cls, event: pygame.event.Event) -> Event:
        try:
            return cls.CLASSES[event.type](**event.__dict__)
        except KeyError:
            raise ValueError(event)

    @classmethod
    @property
    def queue(cls) -> list[Event]:
        return [
            cls.build(event)
            for event in pygame.event.get()
            if event.type in cls.CLASSES
        ]

    @staticmethod
    def make_subclass(name: str, event_type: int, params: list[Parameter]) -> Type:
        sig = Signature(params + [Parameter("kwargs", Parameter.VAR_KEYWORD)])
        subclass = type(name, (Event,), {"type": event_type, "signature": sig})
        Event.CLASSES[event_type] = subclass
        return subclass

    @staticmethod
    def make_pygame_event_classes(**event_types: list[Parameter]) -> None:
        for name, params in event_types.items():
            setattr(
                sys.modules[__name__],
                name,
                Event.make_subclass(name, getattr(pygame, name.upper()), params),
            )


def field(name: str, default: Any = Parameter.empty):
    return Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, default=default)


Event.make_pygame_event_classes(
    KeyDown=[field("key"), field("mod", default=0)],
    KeyUp=[field("key"), field("mod", default=0)],
    MouseButtonDown=[field("button", default=1)],
    MouseButtonUp=[field("button", default=1)],
    MouseMotion=[field("buttons", default=(0, 0, 0))],
    Quit=[],
)
