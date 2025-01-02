from dataclasses import dataclass

import pygame


@dataclass
class Spritesheet:
    """A class to represent a spritesheet.

    >>> _ = pygame.init()
    >>> _ = pygame.display.set_mode((100, 50))
    >>> image = pygame.Surface((100, 50))
    >>> colors = "red yellow green brown blue pink black white".split()
    >>> coords = [(x, y) for y in range(2) for x in range(4)]
    >>> name_map = dict(zip(colors, coords))
    >>> for i, (color, (x, y)) in enumerate(name_map.items()):
    ...     pygame.draw.rect(image, colors[i], (x * 25, y * 25, 25, 25))
    Rect(0, 0, 25, 25)
    ...
    >>> sheet = Spritesheet(image, rows=2, columns=4, name_map=name_map)
    >>> all(
    ...     all(
    ...         sheet[color].get_at((x, y)) == pygame.Color(color)
    ...         for x in range(25) for y in range(25)
    ...     )
    ...     for color in colors
    ... )
    True
    """

    image: pygame.Surface
    rows: int = 1
    columns: int = 1
    name_map: dict[str, tuple[int, int]] | None = None

    def __post_init__(self) -> None:
        self.grid_size = pygame.Vector2(self.columns, self.rows)

    @property
    def cell_size(self) -> tuple[int, int]:
        if not hasattr(self, "_cell_size"):
            width, height = self.image.get_size()
            self._cell_size = (width // self.columns, height // self.rows)
        return self._cell_size

    def __getitem__(self, key: str | tuple[int, int]) -> pygame.Surface:
        match key:
            case str(skey) if self.name_map and (coord := self.name_map[skey]):
                return self[coord]

            case tuple(t) if (0 <= t[0] < self.columns and 0 <= t[1] < self.rows):
                cell_w, cell_h = self.cell_size
                pos = (t[0] * cell_w, t[1] * cell_h)
                return self.image.subsurface((pos, self.cell_size))

        raise KeyError
