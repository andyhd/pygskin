"""Direction enum class for representing directions in a 2D grid."""

from __future__ import annotations

from enum import IntFlag

from pygame import Vector2


class Direction(IntFlag):
    """Direction enum class for representing directions in a 2D grid."""

    UP = 1
    RIGHT = 2
    DOWN = 4
    LEFT = 8

    VERTICAL = 5
    HORIZONTAL = 10

    @property
    def axis(self) -> Direction:
        """Return the axis of the direction."""
        if self in Direction.VERTICAL:
            return Direction.VERTICAL
        if self in Direction.HORIZONTAL:
            return Direction.HORIZONTAL
        return Direction(0)

    @property
    def vector(self) -> Vector2:
        """Return the unit vector of the direction."""
        return {
            self.UP: Vector2(0, -1),
            self.DOWN: Vector2(0, 1),
            self.LEFT: Vector2(-1, 0),
            self.RIGHT: Vector2(1, 0),
        }[self]
