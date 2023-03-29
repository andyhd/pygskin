from typing import Any
from typing import Callable
from typing import ClassVar

import pygame

from pygskin.events import Event
from pygskin.pubsub import message


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
