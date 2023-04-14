import re
from typing import Iterable

import pygame

WORD_START = re.compile(r"(?<!^)(?=[A-Z])")


def to_snake_case(s):
    return WORD_START.sub("_", s).lower()


def rotate(
    surface: pygame.Surface,
    angle: float,
    center: Iterable[float],
    offset: Iterable[float],
) -> tuple[pygame.Surface, pygame.Rect]:
    rotated_surface = pygame.transform.rotate(surface, angle)
    rotated_offset = pygame.math.Vector2(offset).rotate(-angle)
    rect = rotated_surface.get_rect(center=center + rotated_offset)
    return rotated_surface, rect
