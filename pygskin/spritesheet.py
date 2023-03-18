from dataclasses import dataclass
from dataclasses import field
from functools import cache

import pygame

from pygskin.grid import Grid


@dataclass
class Spritesheet:
    image: pygame.Surface
    grid: Grid
    names: dict[str, tuple[int, int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.rect = self.image.get_size()
        self.grid.map_to(self.rect)

    def __getitem__(self, key: str | tuple[int, int]) -> pygame.Surface:
        if isinstance(key, str):
            skey = str(key)
            if self.names and skey in self.names:
                return self[self.names[skey]]

        if isinstance(key, tuple):
            return self.image.subsurface(self.grid.rect(key))

        raise KeyError


class CachedSpritesheet(Spritesheet):
    @cache
    def __getitem__(self, key: str | tuple[int, int]) -> pygame.Surface:
        return super().__getitem__(key)
