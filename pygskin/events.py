"""Event classes."""
from __future__ import annotations

from inspect import Parameter
from inspect import Signature
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import _GenericAlias

import pygame

from pygskin import ecs
from pygskin.pubsub import message


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


class Timer(Event):
    """
    Timer event adds itself to the event queue after `delay` milliseconds.
    If `repeat_count` is > 1, it adds itself to the event queue that many times at
    `delay`ms intervals.
    If `repeat_cound` is 0 (Timer.REPEAT_FOREVER), it will continuously add itself to
    the queue at `delay`ms intervals.
    Repeat events can be stopped with `cancel()`
    """

    REPEAT_FOREVER: ClassVar[int] = 0
    ONCE: ClassVar[int] = 1

    _CUSTOM_TYPES_POOL: ClassVar[set[int]] = set()
    _CUSTOM_TYPES_IN_USE: ClassVar[set[int]] = set()

    delay: int = 0
    repeat_count: int = ONCE
    on_finish: Callable | None = None

    def __post_init__(self) -> None:
        if getattr(self, "type", None) is None:
            self.type = getattr(self, "type_", self._get_custom_type())
        Event.CLASSES[self.type] = self.__class__
        self.finish = message()
        if callable(self.on_finish):
            self.finish.subscribe(self.on_finish)

    def __del__(self) -> None:
        if getattr(self, "type", None) is None:
            return
        try:
            Timer._CUSTOM_TYPES_IN_USE.remove(self.type)
        except KeyError:
            pass
        Timer._CUSTOM_TYPES_POOL.add(self.type)
        try:
            del Event.CLASSES[self.type]
        except KeyError:
            pass
        del self.type

    def match(self, other: Any) -> bool:
        return (
            isinstance(other, (Timer, pygame.event.EventType))
            and other.type in Timer._CUSTOM_TYPES_IN_USE
        )

    def _get_custom_type(self) -> int:
        try:
            type = Timer._CUSTOM_TYPES_POOL.pop()
        except KeyError:
            type = pygame.event.custom_type()
        Timer._CUSTOM_TYPES_IN_USE.add(type)
        return type

    @property
    def event(self) -> pygame.event.Event:
        return pygame.event.Event(
            self.type,
            {
                "type_": self.type,
                "delay": self.delay,
                "repeat_count": self.repeat_count,
                "on_finish": self.on_finish,
            },
        )

    @message
    def start(self) -> None:
        """Trigger the event (sequence)."""
        pygame.time.set_timer(
            self.event,
            millis=self.delay,
            loops=self.repeat_count,
        )

    def repeat(self, repeat_count: int = REPEAT_FOREVER) -> None:
        """Set repeat count and trigger the event sequence."""
        self.repeat_count = repeat_count
        self.start()

    def cancel(self) -> None:
        """Cancel the timer."""
        pygame.time.set_timer(
            self.event,
            millis=0,
        )


class EventMap(dict[Event, Callable[[], None]]):
    """Add this component to entities that need to track events."""


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
