from __future__ import annotations

import functools
import math
import re
from collections.abc import Callable
from typing import Any
from typing import Iterable
from typing import Self
from typing import overload

import pygame
from pygame.math import Vector2

WORD_START = re.compile(r"(?<!^)(?=[A-Z])")


def to_snakecase(string: str):
    return WORD_START.sub("_", string).lower()


def snakecase_to_capwords(snakecase: str) -> str:
    return "".join(word.capitalize() for word in snakecase.split("_"))


def rotate(
    surface: pygame.Surface,
    angle: float,
    center: pygame.Vector2,
    offset: pygame.Vector2 | None = None,
) -> tuple[pygame.Surface, pygame.Rect]:
    rotated_surface = pygame.transform.rotate(surface, angle)
    offset = offset.rotate(-angle) if offset else pygame.Vector2(0)
    rect = rotated_surface.get_rect(center=center + offset)
    return rotated_surface, rect


def angle_between(v1: Vector2, v2: Vector2) -> float:
    """
    Calculate the angle from v1 to v2
    0 degrees is down and angle increases anti-clockwise, due to pygame's
    inverted y coordinate system.

    >>> points = [(1, 5), (4, 5), (4, 2), (4, -1), (1, -1), (-2, -1), (-2, 2), (-2, 5)]
    >>> [angle_between(Vector2(1, 2), Vector2(b)) for b in points]
    [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]
    """
    return math.degrees(math.atan2((v2.x - v1.x), (v2.y - v1.y))) % 360


class Decorator:
    @overload
    def __init__(self, fn: Callable) -> None:
        ...

    def __init__(self, *args, **kwargs) -> None:
        self.obj = kwargs.get("obj")
        self.fn: Callable | None = None
        self.name: str | None = None
        self.args: list = []
        self.kwargs: dict = {}

        if len(args) == 1 and callable(args[0]):
            self.set_function(args[0])
        else:
            self.set_args(*args, **kwargs)

    def set_function(self, fn: Callable) -> None:
        self.fn = fn

    def set_args(self, *args, **kwargs) -> None:
        self.args = list(args)
        self.kwargs = dict(kwargs)

    @overload
    def __call__(self, fn: Callable) -> Self:
        ...

    def __call__(self, *args, **kwargs) -> Any:
        if not self.fn and len(args) == 1 and callable(args[0]):
            self.set_function(args[0])
            return self

        return self.call_function(*args, **kwargs)

    def call_function(self, *args, **kwargs) -> Any:
        return self.fn(*args, **kwargs)

    def __get__(self, obj: Any, obj_type: Any = None) -> Self:
        if obj and obj != self.obj:
            fn = None
            if self.fn:
                fn = functools.partial(self.fn, obj)
            decorator = type(self)(fn, obj=obj)
            decorator.set_args(*self.args, **self.kwargs)
            setattr(obj, self.name, decorator)
            return decorator
        return self

    def __set_name__(self, owner: Any, name: str) -> None:
        self.name = name


def make_sprite(image: pygame.surface.Surface, **kw) -> pygame.sprite.Sprite:
    """Make a sprite object from a Surface."""
    spr = pygame.sprite.Sprite()
    if bg_color := kw.pop("bg_color", None):
        image.fill(bg_color)
    if scale := kw.pop("scale", None):
        image = pygame.transform.scale_by(image, scale)
    spr.image = image
    spr.rect = image.get_rect(**kw)
    return spr


class Padding:
    def __init__(self, padding: int | Iterable[int] = 0) -> None:
        self.default = padding
        if isinstance(padding, int):
            self.top = self.right = self.bottom = self.left = padding

        else:
            try:
                padding = iter(padding)
                self.top = self.right = self.bottom = self.left = next(padding)
                self.right = self.left = next(padding)
                self.bottom = next(padding)
                self.left = next(padding)
            except StopIteration:
                pass

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} top={self.top}, right={self.right}, "
            f"bottom={self.bottom}, left={self.left}>"
        )

    def __iter__(self) -> Iterable[int]:
        yield from [self.top, self.right, self.bottom, self.left]

    def __set_name__(self, _, name: str) -> None:
        self._name = f"_{name}"

    def __get__(self, obj, type) -> Padding:
        if obj is None:
            return self
        return getattr(obj, self._name, Padding(padding=self.default))

    def __set__(self, obj, value) -> None:
        setattr(obj, self._name, Padding(padding=value))

    @property
    def width(self) -> int:
        return self.left + self.right

    @property
    def height(self) -> int:
        return self.top + self.bottom
