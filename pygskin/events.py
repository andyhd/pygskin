from __future__ import annotations

import inspect
import types
import typing
from collections.abc import Callable
from collections.abc import Iterable
from typing import Any
from typing import ClassVar
from typing import overload

import pygame

from pygskin import ecs
from pygskin.direction import Direction
from pygskin.utils import Decorator


class Event:
    TYPE_MAP: ClassVar[dict[int, type[Event]]] = {}
    event_type: ClassVar[int | None] = None
    cancelable: ClassVar[bool] = True

    @overload
    def __init__(self, event: pygame.event.Event) -> None:
        ...

    @overload
    def __init__(self, metadata: dict[str, Any] | None = None, **kwargs) -> None:
        ...

    def __init__(self, *args, **kwargs) -> None:
        match args:
            case (pygame.event.Event() as event,):
                if self.event_type is None or event.type != self.event_type:
                    raise ValueError(
                        f"{self.__class__.__name__} got unexpected event type: {event}"
                    )
                self.metadata = set(event.__dict__.items())

            case (dict() as metadata,):
                self.metadata = metadata

            case _:
                self.metadata = kwargs

        self.__dict__.update(self.metadata)
        self.cancelled = False

    def __init_subclass__(cls, **kwargs) -> None:
        _type = kwargs.get("event_type")

        cls.event_type = int(_type) if _type is not None else pygame.event.custom_type()

        Event.TYPE_MAP[cls.event_type] = cls

    @classmethod
    def build(cls, event: pygame.event.Event) -> Event | None:
        if event_class := Event.TYPE_MAP.get(event.type):
            # XXX avoid recursion
            if "build" in cls.__dict__:
                return event_class.build(event)
            return event_class(event)

    def cancel(self) -> None:
        if self.cancelable:
            self.cancelled = True

    def post(self) -> bool:
        return pygame.event.post(
            pygame.event.Event(self.event_type, dict(self.metadata))
        )


class KeyEvent(Event):
    KEY_MAP = {
        value: f'{"_" if name[2:].isdigit() else ""}{name[2:].upper()}'
        for name, value in pygame.__dict__.items()
        if name.startswith("K_") and name not in ("K_LAST",)
    }

    def __init__(self, *args, **kwargs) -> None:
        match args:
            case (pygame.event.Event() as event,):
                if event.type != self.event_type or event.key != self.key:
                    raise ValueError(
                        f"{self.__class__.__name__} got unexpected event type: {event}"
                    )

        super().__init__(*args, **kwargs)

    def __init_subclass__(cls, **kwargs) -> None:
        if "event_type" in kwargs:
            super().__init_subclass__(**kwargs)
            cls.KEY_MAP = {}
            direction_names = {d.name for d in Direction}
            for key_code, key_name in KeyEvent.KEY_MAP.items():
                attrs = {"key": key_code}
                if key_name in direction_names:
                    attrs["direction"] = Direction[key_name]
                subclass = type(f"{cls.__name__}.{key_name}", (cls,), attrs)
                cls.KEY_MAP[key_code] = subclass
                setattr(cls, key_name, subclass)

    @classmethod
    def build(cls, event: pygame.event.Event) -> Event | None:
        if event.type == cls.event_type and (event_class := cls.KEY_MAP.get(event.key)):
            return event_class(event)


class KeyDown(KeyEvent, event_type=pygame.KEYDOWN):
    pass


class KeyUp(KeyEvent, event_type=pygame.KEYUP):
    pass


class MouseButtonDown(Event, event_type=pygame.MOUSEBUTTONDOWN):
    pass


class MouseButtonUp(Event, event_type=pygame.MOUSEBUTTONUP):
    pass


class MouseMotion(Event, event_type=pygame.MOUSEMOTION):
    pass


class Quit(Event, event_type=pygame.QUIT):
    pass


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
            event = kwargs["event"]
            if event and event.cancelled:
                break
            if isinstance(value, EventListener):
                getattr(entity, attr)(event)
