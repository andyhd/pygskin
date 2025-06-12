"""Access cells in a spritesheet."""

from collections.abc import Callable
from functools import cache

import pygame
from pygame import Surface

from pygskin.rect import grid


def spritesheet(image: Surface, *args, **kwargs) -> Callable[..., Surface]:
    """Return a function to access cells in a spritesheet.

    >>> image = Surface((20, 10))
    >>> colors = {"r": [255, 0, 0, 255], "g": [0, 255, 0, 255], "b": [0, 0, 255, 255]}
    >>> coords = [(x, 0) for x in range(3)]
    >>> names = dict(zip(colors.keys(), coords))
    >>> for i, (color, (x, y)) in enumerate(names.items()):
    ...     image.fill(colors[color], (x * 5, y * 5, 5, 5))
    Rect(0, 0, 5, 5)
    ...
    >>> sheet = spritesheet(image, rows=1, columns=3, names=names)
    >>> all(list(sheet(name).get_at((0, 0))) == color for name, color in colors.items())
    True
    """

    scale_factor = kwargs.pop("scale_by", 1)
    get_cell = grid(image.get_rect(), *args, **kwargs)

    @cache
    def get_subsurface(*args, **kwargs) -> Surface:
        return pygame.transform.scale_by(
            image.subsurface(get_cell(*args, **kwargs)),
            scale_factor,
        )

    get_subsurface.columns = kwargs.get("columns", 1)
    get_subsurface.rows = kwargs.get("rows", 1)

    return get_subsurface
