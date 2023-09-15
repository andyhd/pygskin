from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from typing import Iterable

import pygame

from pygskin import ecs
from pygskin.pubsub import message


class TickHandler(message):
    pass


on_tick = TickHandler


class Clock(ecs.System):
    _clock = pygame.time.Clock()
    delta_time: float = 0
    options: dict = {}

    def __init__(self, **options) -> None:
        Clock.options.update(options)
        Clock.delta_time = 0

    @classmethod
    def filter(cls, entity: ecs.Entity) -> bool:
        return entity.has(TickHandler)

    @classmethod
    def update(cls, entities: Iterable[ecs.Entity], **kwargs) -> None:
        cls.delta_time = cls._clock.tick(cls.options.setdefault("fps", 60))
        kwargs["delta_time"] = cls.delta_time
        for entity in filter(cls.filter, entities):
            cls.update_entity(entity, **kwargs)

    @classmethod
    def update_entity(cls, entity: ecs.Entity, **kwargs) -> None:
        entity.TickHandler(cls.delta_time, **kwargs)


@dataclass
class Timer(ecs.Entity):
    seconds: float = 0.0
    on_expire: Callable | None = None
    delete: bool = True

    def __post_init__(self) -> None:
        ecs.Entity.__init__(self)

        if callable(self.on_expire):
            self.end.subscribe(self.on_expire)

        self.reset()

    def reset(self) -> None:
        self.remaining = self.seconds * 1000
        self.started = False
        self.paused = True
        self.ended = False

    @message
    def start(self) -> None:
        self.remaining = self.seconds * 1000
        self.started = True
        self.paused = False
        self.ended = False

    @message
    def end(self) -> None:
        if not self.ended and self.delete:
            ecs.Entity.instances.remove(self)
        self.ended = True
        self.started = False

    @message
    def cancel(self) -> None:
        if not self.ended and self.delete:
            ecs.Entity.instances.remove(self)
        self.ended = True
        self.started = False

    @on_tick
    def update(self, dt: int, **_) -> None:
        if self.started and not (self.ended or self.paused):
            self.remaining -= dt
            if self.remaining <= 0:
                self.end()

    @message
    def pause(self) -> None:
        if self.started and not self.ended:
            self.paused = True

    @message
    def resume(self) -> None:
        if (self.started and not self.ended) and self.paused:
            self.paused = False

    @classmethod
    def factory(cls, seconds: float = 0.0) -> Callable[[], Timer]:
        return lambda: Timer(seconds)


# class IntervalSystem(TickSystem):
#     interval = 0

#     def __init__(self, **options):
#         super().__init__(**options)
#         self.timer = self.interval

#     def should_update(self, **kwargs) -> bool:
#         self.timer -= self.ms_since_last_tick
#         if self.timer <= 0:
#             self.timer = self.interval
#             return True
#         return False
