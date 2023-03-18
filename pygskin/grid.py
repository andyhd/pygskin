from dataclasses import dataclass
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

    def __contains__(self, xy: tuple[int, int]) -> bool:
        x, y = xy
        return 0 <= y < self.rows and 0 <= x < self.cols

    def rect(self, xy: tuple[int, int]) -> Rect:
        return Rect(self.map(xy), self.cell_size)

    def neighbours(self, x, y) -> Iterator[tuple[int, int]]:
        for j in (-1, 0, 1):
            for i in (-1, 0, 1):
                if not i == j == 0:
                    yield (x + i, y + j)
