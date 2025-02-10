from collections.abc import Callable
from functools import cache

from pygame import Surface
from pygame.math import Vector2
from pygame.transform import rotate
from pygame.typing import Point


def draw_sprite_stack(
    surface: Surface,
    sprite_stack: Callable[..., Surface],
    center: Point,
    angle: int = 0,
    spacing: int = 1,
) -> None:
    rotate_slice = cache(lambda i: rotate(sprite_stack(i, 0), angle))
    center = Vector2(center)

    surface.blits((
        (slice, slice.get_rect(center=center - (0, i * spacing)))
        for i, slice in enumerate(map(rotate_slice, range(sprite_stack.columns)))
    ))
