"""Event classes."""
from __future__ import annotations

from inspect import Parameter
from inspect import Signature
from typing import Any
from typing import ClassVar
from typing import _GenericAlias

import pygame


def is_classvar(a_type) -> bool:
    return a_type is ClassVar or (
        type(a_type) is _GenericAlias and a_type.__origin__ is ClassVar
    )


class EventBase(type):
    """
    Event metaclass.

    Enables definition of Event classes similar to dataclasses. Class definition should
    be a list of attributes corresponding to the pygame event. The pygame event id
    number is derived from the class name (eg: KeyDown -> pygame.KEYDOWN).
    """

    def __new__(cls, name, bases, attrs):
        """Construct a new Event class."""

        # exclude Event class, only modify subclasses
        parents = [b for b in bases if isinstance(b, EventBase)]
        if not parents:
            return super().__new__(cls, name, bases, attrs)

        signature = Signature(
            [
                Parameter(
                    name,
                    Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=annotation,
                    default=attrs.get(name, Parameter.empty),
                )
                for name, annotation in attrs.get("__annotations__", {}).items()
                if not is_classvar(annotation)
            ]
            + [Parameter("kwargs", Parameter.VAR_KEYWORD)]
        )

        def init_fn(self, *args, **kwargs) -> None:
            params = signature.bind(*args, **kwargs)
            params.apply_defaults()
            kwargs = params.arguments.pop("kwargs", {})
            self.__dict__.update(params.arguments)
            self.__dict__.update(kwargs)
            self._ignore = False
            if hasattr(self, "__post_init__") and callable(self.__post_init__):
                self.__post_init__()

        attrs["__init__"] = init_fn
        attrs["type"] = getattr(pygame, name.upper(), None)
        new_class = super().__new__(cls, name, bases, attrs)
        if isinstance(new_class.type, int):
            Event.CLASSES[new_class.type] = new_class
        return new_class


class Event(metaclass=EventBase):
    """
    Base event class.

    Provides a lookup of event type id numbers to Event subclasses, a factory method to
    build an Event subclass from a pygame event object, and a wrapper around
    pygame.event.get to get a list of Event objects.

    Event objects are equal if one event object's attributes are a subset of the
    other's. This enables an EventMap to match a whole class of events.
    """

    CLASSES: ClassVar[dict[int, type[Event]]] = {}

    def match(self, other: Any) -> bool:
        """Return True if this event's attributes are a subset of other's."""
        return (
            isinstance(other, (Event, pygame.event.Event, pygame.event.EventType))
            and self.type == other.type
            and self.__dict__.items() <= other.__dict__.items()
            and not self._ignore
        )

    def __eq__(self, other: Any) -> bool:
        """Override the equality operator to enable EventMap."""
        return self.match(other)

    def __hash__(self) -> int:
        """Allow hashing event objects for use in EventMap keys."""
        return hash((self.type, repr(self.__dict__)))

    def stop_propagation(self) -> None:
        """Prevent this event from being handled."""
        self._ignore = True

    @classmethod
    def build(cls, event: pygame.event.Event) -> Event:
        """Build an Event object from a pygame event."""
        try:
            return cls.CLASSES[event.type](**event.__dict__)
        except KeyError:
            raise ValueError(event)

    @classmethod
    @property
    def queue(cls) -> list[Event]:
        """Return a list of Event objects for pygame events since last call."""
        return [
            cls.build(event)
            for event in pygame.event.get()
            if event.type in cls.CLASSES
        ]


class KeyDown(Event):
    key: int
    mod: int = 0


class KeyUp(Event):
    key: int
    mod: int = 0


class MouseButtonDown(Event):
    button: int = 1


class MouseButtonUp(Event):
    button: int = 1


class MouseMotion(Event):
    buttons: tuple[int, int, int] = (0, 0, 0)


class Quit(Event):
    pass
