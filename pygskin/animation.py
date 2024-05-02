from dataclasses import dataclass
from operator import itemgetter
from typing import Any
from typing import Mapping
from typing import Protocol
from typing import TypeVar
from typing import runtime_checkable

import pygame

from pygskin.easing import EasingFunction
from pygskin.statemachine import StateMachine

Frame = TypeVar("Frame")
Keyframes = Mapping[float, Frame | tuple[Frame, EasingFunction]]


@runtime_checkable
class HasLerp(Protocol[Frame]):
    """Provides a lerp method."""

    def lerp(self: Frame, other: Frame, quotient: float) -> Frame:
        ...


@runtime_checkable
class Lerpable(Protocol[Frame]):
    """Can be plugged into standard linear interpolation algorithm."""

    def __add__(self: Frame, other: Frame) -> Frame:
        ...

    def __mul__(self: Frame, other: float) -> Frame:
        ...

    def __sub__(self: Frame, other: Frame) -> Frame:
        ...


class Animation(Protocol):
    duration: float

    def frame_at(self, index: float) -> Any:
        ...


@dataclass
class KeyframeAnimation(Animation):
    """
    Mapping of indexes to key Frames.

    >>> anim = KeyframeAnimation({
    ...     0: {"x": 2},
    ...     1: {"x": 8},
    ...     2: {"x": 3},
    ... })
    >>> anim.frame_at(0)
    {'x': 2.0}
    >>> anim.frame_at(0.5)
    {'x': 5.0}
    >>> anim.frame_at(1)
    {'x': 8.0}
    >>> anim.frame_at(1.5)
    {'x': 5.5}
    """

    keyframes: Keyframes

    def __post_init__(self) -> None:
        self.keyframes, self.duration = self._sort_keyframes()
        self.lerp_fn = self._lerp

    def _sort_keyframes(self) -> tuple[Keyframes, float]:
        max_index = 0.0
        keyframes = {}
        for index, frame in sorted(self.keyframes.items(), key=itemgetter(0)):
            max_index = max(index, max_index)
            easing = None
            if isinstance(frame, tuple) and len(frame) == 2 and callable(frame[1]):
                frame, easing = frame
            keyframes[index] = (frame, easing)
        return keyframes, max_index

    def frame_at(self, index: float) -> Any:
        start = end = easing = None

        for i, (frame, fn) in self.keyframes.items():
            if i <= index:
                start, start_frame, easing = i, frame, fn
                continue
            if i >= index:
                end, end_frame, easing = i, frame, fn
                break

        if start is None:
            return end_frame

        if end is None:
            return start_frame

        duration = end - start
        progress = (index - start) / duration

        if easing:
            progress = easing(progress)

        return self.lerp(start_frame, end_frame, progress)

    def __getitem__(self, index: float) -> Any:
        return self.frame_at(index)

    def lerp(self, start: Any, end: Any, quotient: float) -> Any:
        return self.lerp_fn(start, end, quotient)

    def _lerp(self, start: Any, end: Any, quotient: float) -> Any:
        if isinstance(start, dict):
            return {
                key: self._lerp(val, end[key], quotient) for key, val in start.items()
            }

        if isinstance(start, HasLerp):
            return start.lerp(end, quotient)

        if isinstance(start, Lerpable):
            return start + quotient * (end - start)

        return start


class Player:
    def __init__(self, animation: Animation, loops: float = 0) -> None:
        self._statemachine = StateMachine(
            {
                "not started": [self.start],
                "running": [self.pause, self.stop],
                "paused": [self.resume, self.stop],
                "stopped": [self.loop],
            }
        )
        self._elapsed: float = 0
        self._start_ticks: float = 0
        self.animation = animation
        self.duration: float = animation.duration
        self.loops: float = loops or 0

    @property
    def current_frame(self) -> Any:
        self.send(None)
        return self.animation.frame_at(self.elapsed)

    @property
    def elapsed(self) -> float:
        match self._statemachine.state:
            case "stopped":
                return self.duration
            case "paused":
                return self._elapsed
            case "running":
                return pygame.time.get_ticks() - self._start_ticks
        return 0

    def send(self, input_: str | None) -> None:
        self._statemachine.send(input_)

    def start(self, input_: str | None, *_) -> str | None:
        if input_ == "start":
            self._start_ticks = pygame.time.get_ticks()
            return "running"
        return None

    def pause(self, input_: str | None) -> str | None:
        if input_ == "pause":
            self._elapsed = self.elapsed
            return "paused"
        return None

    def resume(self, input_: str | None) -> str | None:
        if input_ == "resume":
            self._start_ticks = pygame.time.get_ticks() - self._elapsed
            return "running"
        return None

    def stop(self, input_: str | None) -> str | None:
        if input_ == "stop" or self.elapsed >= self.duration:
            return "stopped"
        return None

    def loop(self, *_) -> str | None:
        if self.loops > 0:
            self.loops -= 1
            self._elapsed = 0
            return self.resume("resume")
        return None
