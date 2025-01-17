"""
Provides a function to scroll the layers of the parallax effect by a given vector.
"""

from collections.abc import Callable
from collections.abc import Iterable

from pygame.sprite import Sprite
from pygame.typing import Point


def scroll_parallax_layers(
    vector: Point,
    get_layers: Callable[[], Iterable[int]],
    get_sprites_from_layer: Callable[[int], Iterable[Sprite]],
    speeds: dict[int, float],
) -> None:
    """Scroll the layers of the parallax effect by the given vector."""
    vx, vy = vector[0], vector[1]
    layers = get_layers()
    for layer in layers:
        speed = speeds.get(layer, 1)
        lvx, lvy = vx * speed, vy * speed
        for sprite in get_sprites_from_layer(layer):
            if rect := sprite.rect:
                rect.move_ip(lvx, -lvy)
                rect.x %= rect.width
                rect.y %= rect.height
