from dataclasses import dataclass
from typing import Iterable
from typing import Iterator

from pygame import Rect


@dataclass
class Grid:
    cols: int
    rows: int

    def __post_init__(self) -> None:
        self.size = self.mapped_size = (self.cols, self.rows)
        self._cell_size = (1, 1)

    def map_to(self, other: tuple[int, int]) -> None:
        width, height = self.mapped_size = other
        grid_width, grid_height = self.size
        self._cell_size = (width // grid_width, height // grid_height)

    @property
    def cell_size(self) -> tuple[int, int]:
        return self._cell_size

    @cell_size.setter
    def cell_size(self, size: tuple[int, int]) -> None:
        cell_width, cell_height = self._cell_size = size
        self.mapped_size = self.map(self.size)

    def map(self, xy: tuple[int, int]) -> tuple[int, int]:
        x, y = xy
        cell_width, cell_height = self.cell_size
        return (x * cell_width, y * cell_height)

    def __iter__(self) -> Iterator[tuple[int, int]]:
        for row in range(self.rows):
            for col in range(self.cols):
                yield (col, row)

    def __contains__(self, xy: Iterable[int]) -> bool:
        x, y = xy
        return 0 <= y < self.rows and 0 <= x < self.cols

    def rect(self, xy: tuple[int, int]) -> Rect:
        return Rect(self.map(xy), self.cell_size)

    def neighbours(self, x, y, wrap: bool = False) -> Iterator[tuple[int, int]]:
        wrap_x = wrap_y = wrap
        rows = (y - 1, y, y + 1)
        if wrap_y:
            rows = [(y % self.rows) for y in rows]
        cols = (x - 1, x, x + 1)
        if wrap_x:
            cols = [(x % self.cols) for x in cols]
        for ny in rows:
            for nx in cols:
                if not (ny == y and nx == x):
                    yield (nx, ny)
