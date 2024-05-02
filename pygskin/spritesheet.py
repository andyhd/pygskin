from __future__ import annotations

from collections.abc import Callable
from functools import cache
from typing import TypeAlias

import pygame

LazyImage: TypeAlias = Callable[[], pygame.Surface]
Image: TypeAlias = pygame.Surface | LazyImage
Grid: TypeAlias = tuple[int, int]
Coord: TypeAlias = tuple[int, int]
NameMap: TypeAlias = dict[str, tuple[int, int]] | None


class Spritesheet:
    def __init__(self, image: Image, grid: Grid, name_map: NameMap = None) -> None:
        self._image = image
        self.grid = grid
        self.name_map = name_map or {}

    @property
    def image(self) -> pygame.Surface:
        if callable(self._image):
            self._image = self._image()
        return self._image

    @cache
    def __getitem__(self, key: str | Coord) -> pygame.Surface:
        if isinstance(key, str) and (coord := self.name_map[key]):
            return self[coord]

        if isinstance(key, tuple):
            grid_width, grid_height = self.grid
            x, y = key

            if not (0 <= x < grid_width and 0 <= y < grid_height):
                raise KeyError

            cell_size = self.__dict__.setdefault(
                "_cell_size",
                self.__dict__.setdefault(
                    "_image_size", pygame.Vector2(self.image.get_size())
                ).elementwise()
                // self.grid,
            )

            return self.image.subsurface((cell_size.elementwise() * key, cell_size))

        raise KeyError
