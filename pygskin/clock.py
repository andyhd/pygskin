from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pygame

from pygskin.pubsub import message


class Clock:
    delta_time: float = 0
    _clock = pygame.time.Clock()

    @classmethod
    def tick(cls, fps: int = 60) -> float:
        cls.delta_time = dt = cls._clock.tick(fps)
        return dt


@dataclass
class Timer:
    seconds: float = 0.0
    on_expire: Callable | None = None
    delete: bool = False

    def __post_init__(self) -> None:
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
        self.ended = True
        self.started = False

    @message
    def cancel(self) -> None:
        self.ended = True
        self.started = False

    def update(self, **_) -> None:
        if self.started and not (self.ended or self.paused):
            self.remaining -= Clock.delta_time
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
