"""Shake effect for camera or other objects."""

import math
from random import uniform

from pygame import Vector2


def shake(
    dampening: float = 0.3,
    direction: Vector2 | None = None,
    magnitude: float = 20,
    noise: float = 1.0,
):
    """Create a shake effect function."""
    if direction is None:
        direction = Vector2(1, 0)

    _magnitude = magnitude

    def _shake(quotient: float) -> Vector2:
        nonlocal _magnitude

        sine_wave = math.sin(quotient)
        _noise = Vector2(uniform(-1, 1), uniform(-1, 1)) * noise
        offset = (direction * sine_wave + _noise).clamp_magnitude(1) * _magnitude
        _magnitude = max(0, _magnitude - dampening)

        return offset

    return _shake
