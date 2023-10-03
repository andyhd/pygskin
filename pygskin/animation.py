from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from typing import Protocol
from typing import TypeVar
from typing import runtime_checkable

from pygskin import ecs
from pygskin.clock import on_tick
from pygskin.pubsub import message

Timestamp = int | float
Frame = TypeVar("Frame")


@runtime_checkable
class Lerpable(Protocol[Frame]):
    """Can be plugged into standard linear interpolation algorithm."""

    def __add__(self: Frame, other: Frame) -> Frame:
        ...

    def __mul__(self: Frame, other: float) -> Frame:
        ...

    def __sub__(self: Frame, other: Frame) -> Frame:
        ...


EasingFunction = Callable[[float], float]


@dataclass
class Animation(ecs.Entity):
    """
    An Animation is a map of timestamps to key Frames.

    >>> anim = Animation({
    ...     0: {"x": 2},
    ...     1: {"x": 8},
    ...     2: {"x": 3},
    ... })
    >>> anim.at(0)
    {'x': 2.0}
    >>> anim.at(0.5)
    {'x': 5.0}
    >>> anim.at(1)
    {'x': 8.0}
    >>> anim.at(1.5)
    {'x': 5.5}
    """

    keyframes: dict[Timestamp, Frame]
    easing: dict[Timestamp, EasingFunction] = field(default_factory=dict)
    lerp_fn: Callable | None = None
    loops: float = 0.0  # float to allow math.inf

    def __post_init__(self) -> None:
        """Ensure keyframes are sorted by timestamp."""
        ecs.Entity.__init__(self)
        self.max_timestamp = 0
        sorted_keyframes = {}
        sorted_easing_fns = {}
        for timestamp in sorted(self.keyframes):
            self.max_timestamp = max(self.max_timestamp, timestamp)
            sorted_keyframes[timestamp] = self.keyframes[timestamp]
            easing_fn = self.easing.get(timestamp)
            if easing_fn:
                sorted_easing_fns[timestamp] = easing_fn
        self.keyframes = sorted_keyframes
        self.easing = sorted_easing_fns
        self.running = False
        self.ended = False
        self.max_loops = self.loops
        self.frame_changed = message()

    def reset(self) -> None:
        """Reset the animation."""
        self.timer = 0
        self.running = False
        self.ended = False
        self.loops = self.max_loops

    def current_frame(self) -> Frame:
        """Get the animation frame at the current timestamp."""
        return self.at(self.timer)

    def at(self, timestamp: Timestamp) -> Frame:
        """Get the animation frame at the specified timestamp."""
        start = None
        end = None
        easing = None

        for ts, frame in self.keyframes.items():
            if ts <= timestamp:
                start, start_frame = ts, frame
                easing = self.easing.get(ts)
                continue
            if ts >= timestamp:
                end, end_frame = ts, frame
                break

        if start is None:
            return end_frame

        if end is None:
            return start_frame

        duration = end - start
        progress = (timestamp - start) / duration

        if easing:
            progress = easing(progress)

        return self.lerp(start_frame, end_frame, progress)

    def lerp(self, start: Frame, end: Frame, quotient: float) -> Frame:
        """Linear interpolation between frame values."""
        if self.lerp_fn:
            return self.lerp_fn(start, end, quotient)
        if isinstance(start, dict):
            return {
                key: self.lerp(val, end[key], quotient) for key, val in start.items()
            }
        if hasattr(start, "lerp"):
            return start.lerp(end, quotient)
        elif isinstance(start, Lerpable):
            return start + quotient * (end - start)
        return start

    def start(self) -> None:
        """Start the animation."""
        if not self.running and not self.ended:
            self.timer = 0
            self.running = True

    def loop(self) -> None:
        """Restart the animation from the beginning."""
        self.loops -= 1
        self.timer = 0

    @message
    def end(self) -> None:
        """Notify subscribers that the animation has ended."""
        self.running = False
        self.ended = True
        self.timer = 0

    @on_tick
    def update(self, dt: int, **kwargs) -> None:
        """Update the animation."""
        if self.running and not self.ended:
            self.timer += dt
            self.frame_changed(self.current_frame())
            if self.timer >= self.max_timestamp:
                if self.loops:
                    self.loop()
                else:
                    self.end()
