"""A 2D camera class."""

from collections.abc import Iterable
from functools import cached_property

import pygame
from pygame import Rect
from pygame import Surface
from pygame import Vector2
from pygame.math import clamp
from pygame.typing import Point
from pygame.typing import RectLike


class Camera:
    """A 2D camera."""

    def __init__(self, rect: Rect | None = None) -> None:
        self.rect = rect or Rect(0, 0, 800, 600)
        self._view: Surface | None = None
        self._zoom = 1.0
        self._original_size = Vector2(self.rect.size)

    @cached_property
    def view(self) -> Surface:
        surface = Surface(self._original_size * (1 / self.zoom))
        self.rect = surface.get_rect(center=self.rect.center)
        return surface

    @property
    def zoom(self) -> float:
        return self._zoom

    @zoom.setter
    def zoom(self, value: float) -> None:
        self._zoom = clamp(value, 0.1, 10)
        del self.view
        _ = self.view

    def blit(self, source: Surface, dest: Point | None = None) -> None:
        if dest is None:
            dest = Vector2()
        self.view.blit(source, Vector2(dest[:2]) - self.rect.topleft)

    def blits(self, blit_sequence: Iterable[tuple[Surface, Point | RectLike]]) -> None:
        blit_seq = [
            (source, Vector2(dest[:2]) - self.rect.topleft)
            for source, dest in blit_sequence
        ]
        return self.view.blits(blit_seq)

    def draw(self, surface: Surface) -> None:
        surface.blit(pygame.transform.scale_by(self.view, self.zoom))
