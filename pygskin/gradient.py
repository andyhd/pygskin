"""
This module provides a function to create a color gradient surface.
"""

from collections.abc import Callable

import pygame
import pygame.constants
from pygame import Color
from pygame import Surface
from pygame.typing import ColorLike
from pygame.typing import Point


def make_color_gradient(
    size: Point,
    start: ColorLike,
    end: ColorLike,
    vertical: bool = True,
    easing_fn: Callable[[float], float] | None = None,
) -> Surface:
    """
    Create a color gradient surface.
    """

    width, height = int(size[0]), int(size[1])

    if vertical:
        positions = zip([0] * height, range(height), strict=True)
        stripe = Surface((1, height), pygame.constants.SRCALPHA)
        quotient = 1 / height
    else:
        positions = zip(range(width), [0] * width, strict=True)
        stripe = Surface((width, 1), pygame.constants.SRCALPHA)
        quotient = 1 / width

    stripe.fill((0, 0, 0, 0))

    for i, pos in enumerate(positions):
        q = i * quotient
        if easing_fn:
            q = easing_fn(q)
        stripe.set_at(pos, Color(start).lerp(Color(end), q))

    return pygame.transform.scale(stripe, (width, height))
