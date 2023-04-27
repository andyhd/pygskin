from __future__ import annotations

from typing import Iterable

import pygame
from pygame import Surface
from pygskin.direction import Direction


Colour = pygame.Color | str | int | tuple[int]
Vector = Iterable[float]


class Gradient:
    def __init__(self, start: Colour, end: Colour) -> None:
        self.start = pygame.Color(start)
        self.end = pygame.Color(end)

    def fill(self, size: Vector, direction: Direction = Direction.DOWN) -> Surface:
        start, end = self.start, self.end
        width, height = size
        if direction in Direction.HORIZONTAL:
            positions = zip(range(width), [0] * width)
            size = (width, 1)
            quotient = 1 / width
        else:
            positions = zip([0] * height, range(height))
            size = (1, height)
            quotient = 1 / height
        if direction in (Direction.UP, Direction.LEFT):
            start, end = end, start
        surface = Surface(size).convert_alpha()
        for i, pos in enumerate(positions):
            surface.set_at(pos, start.lerp(end, i * quotient))
        return pygame.transform.scale(surface, (width, height))
