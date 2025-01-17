"""Rect utility functions."""

from collections.abc import Callable
from collections.abc import Sequence
from typing import overload

from pygame import Rect
from pygame.typing import IntPoint

RECT_ATTRS = """
    x y
    top left bottom right
    topleft bottomleft topright bottomright
    midtop midleft midbottom midright
    center centerx centery
    size width height
    w h
""".strip().split()


def get_rect_attrs(d: dict) -> dict:
    """Return a dictionary with only the keys that are valid Rect attributes."""
    return {k: v for k, v in d.items() if k in RECT_ATTRS}


def add_padding(
    rect: Rect,
    padding: int | Sequence[int] = 0,
) -> tuple[Rect, Rect]:
    """Add padding to a rectangle."""
    match padding:
        case int(px):
            return rect.inflate(px * 2, px * 2), rect.move(px, px)

        case Sequence() as p if 1 <= len(p) <= 4 and all(isinstance(i, int) for i in p):
            try:
                it = iter(p)
                top = right = bottom = left = next(it)
                right = left = next(it)
                bottom = next(it)
                left = next(it)
            except StopIteration:
                pass
            return (
                rect.inflate(left + right, top + bottom).move_to(
                    top=rect.top - top, left=rect.left - left
                ),
                rect.move(left, top),
            )

    raise ValueError("Invalid padding")


def grid(
    rect: Rect,
    rows: int = 1,
    columns: int = 1,
    names: dict[str, IntPoint] | None = None,
) -> Callable[..., Rect]:
    """Return a function to access cells in a grid of rectangles.

    >>> rect = Rect(0, 0, 100, 50)
    >>> get_cell = grid(rect, rows=2, columns=4, names={"foo": (3, 1)})
    >>> get_cell(1, 1)
    Rect(25, 25, 25, 25)
    >>> get_cell("foo")
    Rect(75, 25, 25, 25)
    """

    cellw, cellh = rect.width // columns, rect.height // rows

    @overload
    def get_cell(key: str) -> Rect: ...

    @overload
    def get_cell(column: int, row: int) -> Rect: ...

    def get_cell(*args, **_) -> Rect:
        match args:
            case (str(key),) if names and key in names:
                coord = names[key]
                column, row = coord[0], coord[1]
            case (int(column), int(row)):
                ...
            case _:
                raise KeyError(*args)
        if not (0 <= column < columns and 0 <= row < rows):
            raise KeyError(*args)
        return Rect(column * cellw, row * cellh, cellw, cellh)

    return get_cell
