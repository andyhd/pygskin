"""A simple animation system."""

import math
from bisect import bisect
from collections.abc import Callable
from collections.abc import Iterator
from typing import Generic
from typing import Protocol
from typing import TypeVar
from typing import cast
from typing import runtime_checkable

from pygame import Surface
from pygame.math import clamp

T = TypeVar("T")


EasingFn = Callable[[float], float]
LerpFn = Callable[[T, T, float], T]


@runtime_checkable
class Lerpable(Generic[T], Protocol):
    """Can be plugged into standard linear interpolation algorithm."""

    def __add__(self: T, other: T) -> T: ...

    def __mul__(self: T, other: float) -> T: ...

    def __sub__(self: T, other: T) -> T: ...


def lerp(start, end, quotient):
    """Linear interpolation between two values."""
    if isinstance(start, dict) and isinstance(end, dict):
        return {key: lerp(value, end[key], quotient) for key, value in start.items()}

    if hasattr(start, "lerp") and callable(start.lerp):
        return start.lerp(end, quotient)

    if isinstance(start, Lerpable):
        return start + ((end - start) * quotient)

    # can't interpolate
    return start


def get_keyframe_interpolator(
    keyframes: dict[float, T] | list[T],
    lerp_fn: LerpFn = lerp,
) -> Callable[[float], T]:
    """Get a keyframe interpolator function.

    >>> frames = [2.0, 8.0, 3.0]
    >>> from pygskin import Timer
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

    match keyframes:

        case list():
            num = len(keyframes)
            if num < 2:
                raise ValueError("At least two frames are required")
            keyframes = {i / (num - 1): keyframes[i] for i in range(num)}

        case dict():
            pass

        case _:
            raise TypeError("Invalid keyframes")

    keys = sorted(keyframes.keys())
    if min(keys) < 0.0 or max(keys) > 1.0:
        raise ValueError("Keyframes must span [0, 1]")
    first_key = keys[0]
    last_key = keys[-1]
    last_key_pos = len(keys) - 1

    def get_frame_at(key):
        easing = None
        key_pos = bisect(keys, key)
        start_key = keys[max(0, key_pos - 1)]
        if isinstance(start_frame := keyframes[start_key], tuple):
            start_frame, easing = start_frame

        if start_key == last_key:
            return cast(T, start_frame)

        end_key = keys[min(last_key_pos, key_pos)]
        if isinstance(end_frame := keyframes[end_key], tuple):
            end_frame, _ = end_frame

        if end_key == first_key:
            return cast(T, end_frame)

        duration = end_key - start_key
        quotient = (key - start_key) / duration

        if easing:
            quotient = easing(quotient)

        return lerp_fn(start_frame, end_frame, quotient)

    return get_frame_at


def animate(
    frames: Callable[[float], T] | dict[float, T] | list[T],
    get_quotient: Callable[[], float],
) -> Iterator[T]:
    """
    Animate a sequence of frames.

    >>> import math
    >>> from pygskin import Timer
    >>> timer = Timer(3000)
    >>> anim = animate(lambda q: math.sin(q * math.pi), timer.quotient)
    >>> next(anim)
    0.0
    >>> timer.tick(1500)
    >>> next(anim)
    1.0
    >>> timer.tick(750)
    >>> next(anim)
    0.7071067811865476
    >>> timer.tick(750)
    >>> next(anim)
    1.2246467991473532e-16
    """
    match frames:
        case dict() | list():
            get_frame_at = get_keyframe_interpolator(frames)
        case _ if callable(frames):
            get_frame_at = frames
        case _:
            raise TypeError("Invalid frames")

    while True:
        yield get_frame_at(clamp(get_quotient(), 0.0, 1.0))


def get_spritesheet_frames(
    sheet: Callable[..., Surface],
    frames: list[tuple[int, int]]
) -> Callable[[float], Surface]:
    def get_sprite(quotient: float) -> Surface:
        frame_index = math.ceil(quotient * len(frames)) % len(frames)
        return sheet(*frames[frame_index])
    return get_sprite
