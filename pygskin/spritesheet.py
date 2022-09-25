from functools import cache

import pygame


class Spritesheet:
    filename: str
    grid: tuple[int, int]
    names: dict[str, tuple[int, int]]

    def __init__(
        self,
        image: pygame.Surface | None = None,
        grid: tuple[int, int] | None = None,
        names: dict[str, tuple[int, int]] | None = None,
    ) -> None:
        self.image = image or pygame.image.load(self.filename).convert_alpha()
        if grid is not None:
            self.grid = grid
        width, height = self.image.get_size()
        grid_width, grid_height = self.grid
        self.cell_width = int(width / grid_width)
        self.cell_height = int(height / grid_height)

    def __getitem__(self, key: str | tuple[int, int]) -> pygame.Surface:
        if isinstance(key, str):
            skey = str(key)
            if self.names and skey in self.names:
                return self[self.names[skey]]

        if isinstance(key, tuple):
            x, y = key

            image = pygame.Surface((self.cell_width, self.cell_height)).convert_alpha()
            image.blit(
                self.image,
                (0, 0),
                pygame.Rect(
                    x * self.cell_width,
                    y * self.cell_height,
                    self.cell_width,
                    self.cell_height,
                ),
            )
            return image

        raise KeyError


class CachedSpritesheet(Spritesheet):
    @cache
    def __getitem__(self, key: str | tuple[int, int]) -> pygame.Surface:
        return super().__getitem__(key)
