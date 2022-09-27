from functools import cached_property
from typing import Any
from typing import Callable

import pygame
from pygskin import pubsub
from pygskin.events import Event


class Timer(Event):
    REPEAT_FOREVER = 0
    ONCE = 1

    _CUSTOM_TYPES_POOL = set()
    _CUSTOM_TYPES_IN_USE = set()

    def __init__(
        self,
        delay: int,
        repeat_count: int = ONCE,
        on_finish: Callable | None = None,
    ) -> None:
        Event.CLASSES[self.type] = self.__class__
        self.delay = delay
        self.repeat_count = repeat_count
        self.start = pubsub.Message()
        self.start.subscribe(self._start)
        self.finish = pubsub.Message()
        if callable(on_finish):
            self.on_finish = on_finish
            self.finish.subscribe(on_finish)

    def __del__(self) -> None:
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

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, (Timer, pygame.event.EventType))
            and other.type in Timer._CUSTOM_TYPES_IN_USE
        )

    def __hash__(self):
        return hash((self.type, repr(self.event.__dict__)))

    @property
    def event(self) -> pygame.event.Event:
        return pygame.event.Event(
            self.type,
            {
                "delay": self.delay,
                "repeat_count": self.repeat_count,
                "on_finish": self.on_finish,
            },
        )

    @cached_property
    def type(self) -> int:
        try:
            type = Timer._CUSTOM_TYPES_POOL.pop()
        except KeyError:
            type = pygame.event.custom_type()
        Timer._CUSTOM_TYPES_IN_USE.add(type)
        return type

    def _start(self) -> None:
        pygame.time.set_timer(
            self.event,
            millis=self.delay,
            loops=self.repeat_count,
        )

    def repeat(self, repeat_count: int = REPEAT_FOREVER) -> None:
        self.repeat_count = repeat_count
        self.start()

    def cancel(self) -> None:
        pygame.time.set_timer(
            self.event,
            millis=0,
        )
