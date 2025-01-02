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
    for layer in get_layers():
        speed = speeds.get(layer, 1)
        for sprite in get_sprites_from_layer(layer):
            if rect := sprite.rect:
                rect.move_ip(-vx * speed, -vy * speed)
                rect.x %= rect.width
                rect.y %= rect.height

