"""A module for managing the game clock and timers."""

from dataclasses import dataclass

import pygame

Clock = pygame.time.Clock()


@dataclass
class Timer:
    """A timer that ticks milliseconds down to zero."""

    duration: int
    elapsed: int = 0
    paused: bool = False
    loop: int | bool = False

    def __hash__(self) -> int:
        return hash(id(self))

    def tick(self, delta_time: int | None = None) -> None:
        """Advance the timer by a given amount of time."""
        if self.paused:
            return

        delta_time = delta_time or Clock.get_time()
        self.elapsed = min(self.elapsed + delta_time, self.duration)

        if self.finished and self.loop:
            self.elapsed = 0
            if self.loop > 0:
                self.loop -= 1

    def quotient(self) -> float:
        """The proportion of time elapsed."""
        return self.elapsed / self.duration

    @property
    def finished(self) -> bool:
        """Whether the timer has finished."""
        return self.elapsed >= self.duration
