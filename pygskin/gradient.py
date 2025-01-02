import pygame
from pygame import Surface
from pygame.typing import ColorLike
from pygame.typing import Point


def make_color_gradient(
    size: Point,
    start: ColorLike,
    end: ColorLike,
    vertical: bool = True,
    invert: bool = False,
) -> Surface:
    width, height = int(size[0]), int(size[1])

    if vertical:
        positions = zip([0] * height, range(height))
        stripe = Surface((1, height), pygame.SRCALPHA)
        quotient = 1 / height
    else:
        positions = zip(range(width), [0] * width)
        stripe = Surface((width, 1), pygame.SRCALPHA)
        quotient = 1 / width

    stripe.fill((0, 0, 0, 0))

    if invert:
        start, end = end, start

    for i, pos in enumerate(positions):
        stripe.set_at(pos, pygame.Color(start).lerp(pygame.Color(end), i * quotient))

    return pygame.transform.scale(stripe, (width, height))

