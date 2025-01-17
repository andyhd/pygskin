"""Vector utilities."""

import math

from pygame import Vector2


def angle_between(v1: Vector2, v2: Vector2) -> float:
    """
    Calculate the angle from v1 to v2
    0 degrees is down and angle increases anti-clockwise, due to pygame's
    inverted y coordinate system.

    >>> points = [(1, 5), (4, 5), (4, 2), (4, -1), (1, -1), (-2, -1), (-2, 2), (-2, 5)]
    >>> [angle_between(Vector2(1, 2), Vector2(b)) for b in points]
    [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]
    """
    return math.degrees(math.atan2((v2.x - v1.x), (v2.y - v1.y))) % 360
