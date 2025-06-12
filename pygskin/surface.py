"""Surface utilities for Pygame."""

import pygame
from pygame import FRect
from pygame import Rect
from pygame import Surface
from pygame import Vector2
from pygame.sprite import Sprite

from pygskin import get_rect_attrs


def make_sprite(image: Surface, **kw) -> Sprite:
    """Make a sprite object from a Surface."""
    spr = Sprite()
    if bg_color := kw.get("bg_color"):
        image.fill(bg_color)
    if scale := kw.get("scale"):
        image = pygame.transform.scale_by(image, scale)
    spr.image = image
    spr.rect = FRect(image.get_rect(**get_rect_attrs(kw)))
    return spr


def rotate_surface(
    surface: Surface,
    angle: float,
    center: Vector2 | None = None,
    offset: Vector2 | None = None,
) -> tuple[Surface, Rect]:
    """Rotate a surface and return the rotated surface and its rect."""
    rotated_surface = pygame.transform.rotate(surface, angle)
    offset = offset.rotate(-angle) if offset else Vector2(0)
    center = center or Vector2()
    rect = rotated_surface.get_rect(center=center + offset)
    return rotated_surface, rect
