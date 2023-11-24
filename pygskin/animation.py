from dataclasses import dataclass
from operator import itemgetter
from typing import Iterator
from typing import Mapping
from typing import Protocol
from typing import TypeVar
from typing import runtime_checkable

from pygskin import ecs
from pygskin.clock import on_tick
from pygskin.easing import EasingFunction
from pygskin.pubsub import message

Frame = TypeVar("Frame")
Keyframes = Mapping[float, Frame | tuple[Frame, EasingFunction]]


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

    def frame_at(self, index: float) -> Frame:
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
        max_index = 0
        keyframes = {}
        for index, frame in sorted(self.keyframes.items(), key=itemgetter(0)):
            max_index = max(index, max_index)
            easing = None
            if isinstance(frame, tuple) and len(frame) == 2 and callable(frame[1]):
                frame, easing = frame
            keyframes[index] = (frame, easing)
        return keyframes, max_index

    def frame_at(self, index: float) -> Frame:
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

    def __getitem__(self, index: float) -> Frame:
        return self.frame_at(index)

    def lerp(self, start: Frame, end: Frame, quotient: float) -> Frame:
        return self.lerp_fn(start, end, quotient)

    def _lerp(self, start: Frame, end: Frame, quotient: float) -> Frame:
        if isinstance(start, dict):
            return {
                key: self._lerp(val, end[key], quotient) for key, val in start.items()
            }

        if hasattr(start, "lerp"):
            return start.lerp(end, quotient)

        if isinstance(start, Lerpable):
            return start + quotient * (end - start)

        return start


@dataclass
class AnimationPlayer(ecs.Entity):
    animation: Animation
    loops: float = 0.0  # float allows math.inf

    def __post_init__(self) -> None:
        ecs.Entity.__init__(self)
        self._loops = self.loops
        self.reset()

    def reset(self) -> None:
        self.ticks = 0
        self.started = False
        self.running = False
        self.ended = False

    def start(self) -> None:
        if not self.started:
            self.started = True
            self.running = True

    def pause(self) -> None:
        if self.started and not self.ended:
            self.running = False

    def resume(self) -> None:
        if self.started and not self.ended:
            self.running = True

    @message
    def stop(self) -> None:
        if not self.ended:
            self.running = False
            self.ended = True

    @on_tick
    def update(self, dt: int, **_) -> None:
        if self.running:
            if self.ticks >= self.animation.duration:
                if self._loops > 0:
                    self._loops -= 1
                    self.reset()
                    self.start()
                else:
                    self.stop()
            self.ticks += dt

    @property
    def current_frame(self) -> Frame:
        return self.animation.frame_at(self.ticks)

    def frames(self) -> Iterator[Frame]:
        self.start()
        while not self.ended:
            yield self.animation.current_frame
