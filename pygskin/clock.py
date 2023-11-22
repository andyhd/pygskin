from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterable
from dataclasses import dataclass

import pygame

from pygskin import ecs
from pygskin.pubsub import message
from pygskin.utils import Decorator


class TickHandler(Decorator):
    pass


on_tick = TickHandler


class Clock(ecs.System):
    _clock = pygame.time.Clock()
    delta_time: float = 0
    ticks: int = 0
    options: dict = {}

    def __init__(self, **options) -> None:
        super().__init__()
        Clock.options.update(options)
        Clock.delta_time = 0
        Clock.ticks = 0

    @classmethod
    def filter(cls, entity: ecs.Entity) -> bool:
        return entity.has(TickHandler)

    @classmethod
    def update(cls, entities: Iterable[ecs.Entity], **kwargs) -> None:
        dt = cls.delta_time = cls._clock.tick(cls.options.setdefault("fps", 60))
        cls.ticks += dt
        for entity in filter(cls.filter, entities):
            cls.update_entity(entity, dt, **kwargs)

    @classmethod
    def update_entity(cls, entity: ecs.Entity, dt: float, *args, **kwargs) -> None:
        entity.TickHandler(dt, *args, **kwargs)


@dataclass
class Timer(ecs.Entity):
    seconds: float = 0.0
    on_expire: Callable | None = None
    delete: bool = False

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
    def update(self, dt: float, **_) -> None:
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
