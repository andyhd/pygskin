"""Tile an image across a rect."""

from itertools import product

from pygame import Rect
from pygame import Surface
from pygame.sprite import Sprite
from pygame.typing import Point


def tile(
    rect: Rect,
    tile_image: Surface | Sprite,
) -> list[tuple[Surface, Point]]:
    """Get a Surface.blits blit_sequence for tiling an image across the given rect.

    >>> [offset for image, offset in tile(Rect(0, 0, 64, 64), Surface((32, 32)))]
    [(0, 0), (0, 32), (32, 0), (32, 32)]
    """
    match tile_image:
        case Sprite(image=image, rect=tile_rect):
            if not image:
                raise ValueError("tile_image Sprite must have an image attribute")
            if not tile_rect:
                raise ValueError("tile_image Sprite must have a rect attribute")
        case Surface() as image:
            tile_rect = image.get_rect()
        case _:
            raise TypeError("tile_image must be a Surface or Sprite")

    assert tile_rect is not None
    w, h = tile_rect.size
    offsets = (tile_rect.move(x * w, y * h) for x, y in product((-1, 0, 1), repeat=2))
    return [(image, offset.topleft) for offset in offsets if rect.colliderect(offset)]
