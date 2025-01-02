"""A simple animation system."""

from bisect import bisect
from collections.abc import Callable
from collections.abc import Iterator
from typing import Generic
from typing import Protocol
from typing import TypeVar
from typing import cast
from typing import runtime_checkable

import pygame

T = TypeVar("T")


EasingFn = Callable[[float], float]
LerpFn = Callable[[T, T, float], T]


@runtime_checkable
class Lerpable(Generic[T], Protocol):
    """Can be plugged into standard linear interpolation algorithm."""

    def __add__(self: T, other: T) -> T:
        ...

    def __mul__(self: T, other: float) -> T:
        ...

    def __sub__(self: T, other: T) -> T:
        ...


def lerp(start, end, quotient):
    """Linear interpolation between two values."""
    if isinstance(start, dict) and isinstance(end, dict):
        return {
            key: lerp(value, end[key], quotient)
            for key, value in start.items()
        }

    if hasattr(start, "lerp") and callable(start.lerp):
        return start.lerp(end, quotient)

    if isinstance(start, Lerpable):
        return start + ((end - start) * quotient)

    # can't interpolate
    return start


def animate(
    keyframes: dict[float, T | tuple[T, EasingFn]] | list[T],
    get_quotient: Callable[[], float],
    lerp: LerpFn = lerp,
) -> Iterator[T]:
    """
    Get the frame of animation that interpolates between keyframes.

    >>> frames = {
    ...     0.0: 2.0,
    ...     0.5: 8.0,
    ...     1.0: 3.0,
    ... }
    >>> from pygskin import Timer  # doctest: +ELLIPSIS
    >>> timer = Timer(3000)
    >>> anim = animate(frames, timer.quotient)
    >>> next(anim)
    2.0
    >>> timer.tick(1500)
    >>> next(anim)
    8.0
    >>> timer.tick(750)
    >>> next(anim)
    5.5
    >>> timer.tick(750)
    >>> next(anim)
    3.0
    """
    if isinstance(keyframes, list):
        num_frames = len(keyframes)
        if num_frames < 2:
            raise ValueError("At least two frames are required")
        keyframes = {i / (num_frames - 1): keyframes[i] for i in range(num_frames)}

    keys = sorted(keyframes.keys())
    if min(keys) < 0.0 or max(keys) > 1.0:
        raise ValueError("Keyframes must span [0, 1]")

    while True:
        easing = None
        try:
            key = pygame.math.clamp(get_quotient(), 0.0, 1.0)
        except StopIteration:
            return
        key_pos = bisect(keys, key)

        start_key = keys[max(0, key_pos - 1)]
        if isinstance(start_frame := keyframes[start_key], tuple):
            start_frame, easing = start_frame

        if start_key == keys[-1]:
            yield cast(T, start_frame)
            continue

        end_key = keys[min(len(keys) - 1, key_pos)]
        if isinstance(end_frame := keyframes[end_key], tuple):
            end_frame, _ = end_frame

        if end_key == keys[0]:
            yield cast(T, end_frame)
            continue

        duration = end_key - start_key
        quotient = (key - start_key) / duration

        if easing:
            quotient = easing(quotient)

        yield lerp(start_frame, end_frame, quotient)

