"""Layout algorithms."""

from __future__ import annotations

from collections.abc import MutableSequence
from dataclasses import dataclass
from typing import Protocol
from typing import cast
from typing import runtime_checkable

import pygame
from pygame import FRect
from pygame import Rect
from pygame import Vector2

from pygskin.direction import Direction


class HasRect(Protocol):
    """Objects that have a pygame.Rect attribute."""

    @property
    def rect(self) -> pygame.rect.Rect | pygame.rect.FRect:
        """Read-only pygame.Rect property."""
        ...


LayoutItems = MutableSequence[HasRect]


@runtime_checkable
class Container(Protocol):
    """Objects that contain other objects in a layout."""

    @property
    def children(self) -> LayoutItems:
        """Sequence of child objects."""
        ...

    @property
    def layout(self) -> Layout:
        """Layout algorithm."""
        ...


class Layout:
    """Base class for callable layout algorithm classes."""

    def __call__(self, bounds: FRect | Rect, items: LayoutItems, **kwargs) -> None:
        """Layout the items inside the bounding Rect."""
        raise NotImplementedError

    @property
    def max_size(self) -> Rect:
        """Get the maximum size of the layout."""
        raise NotImplementedError

    @property
    def min_size(self) -> Rect:
        """Get the minimum size of the layout."""
        raise NotImplementedError

    def calc_preferred_size(self) -> Rect:
        """Calculate the preferred size of the layout."""
        raise NotImplementedError

    @property
    def preferred_size(self) -> Rect:
        """Get the preferred size of the layout."""
        size = self.calc_preferred_size()

        min_size = self.min_size
        max_size = self.max_size

        return Rect(
            0,
            0,
            min(max(size.width, min_size.width), max_size.width),
            min(max(size.height, min_size.height), max_size.height),
        )


@dataclass
class Border(Layout):
    """
    Layout items in five regions: north, south, east, west and center.

    Each region may contain only one item.

    +----------------------+
    |        north         |
    +------+--------+------+
    | west | center | east |
    +------+--------+------+
    |        south         |
    +----------------------+
    """

    center: HasRect | None = None
    north: HasRect | None = None
    south: HasRect | None = None
    east: HasRect | None = None
    west: HasRect | None = None

    def __call__(self, bounds: FRect | Rect, items: LayoutItems, **kwargs) -> None:
        """Layout the items in the specified regions."""
        available = bounds.copy()

        if north := self.north:
            north.rect.update(
                bounds.topleft,
                (bounds.width, north.rect.height),
            )

            if isinstance(north, Container):
                north.layout(north.rect, north.children)

            available.top = north.rect.bottom
            available.height -= north.rect.height

        if south := self.south:
            south.rect.update(
                (bounds.left, bounds.bottom - south.rect.height),
                (bounds.width, south.rect.height),
            )

            if isinstance(south, Container):
                south.layout(south.rect, south.children)

            available.height -= south.rect.height

        if west := self.west:
            west.rect.update(
                available.topleft,
                (west.rect.width, available.height),
            )

            if isinstance(west, Container):
                west.layout(west.rect, west.children)

            available.left = west.rect.right
            available.width -= west.rect.width

        if east := self.east:
            east.rect.update(
                (available.right - east.rect.width, available.top),
                (east.rect.width, available.height),
            )

            if isinstance(east, Container):
                east.layout(east.rect, east.children)

            available.width -= east.rect.width

        if center := self.center:
            center.rect.update(available)

            if isinstance(center, Container):
                center.layout(center.rect, center.children)


@dataclass
class Flow(Layout):
    """Layout items next to each other in a line."""

    direction: Direction = Direction.VERTICAL
    #: spacing between items
    spacing: int = 3
    #: wrap items to next row or column
    wrap: bool = False

    def __call__(self, bounds: FRect | Rect, items: LayoutItems, **kwargs) -> None:
        num_items = len(items)

        if num_items == 0:
            return

        offset = Vector2(bounds.topleft)

        maximum = Rect(0, 0, 0, 0)
        for item in items:
            maximum.width = int(max(item.rect.width, maximum.width))
            maximum.height = int(max(item.rect.height, maximum.height))

        for item in items:
            if self.direction == Direction.VERTICAL:
                slot = Rect(offset, (maximum.width, item.rect.height))

                if not bounds.contains(slot) and self.wrap:
                    offset.x += self.spacing + maximum.width
                    offset.y = bounds.top

            else:
                slot = Rect(offset, (item.rect.width, maximum.height))

                if not bounds.contains(slot) and self.wrap:
                    offset.x = bounds.left
                    offset.y += self.spacing + maximum.height

            item.rect.center = slot.center

            if self.direction == Direction.VERTICAL:
                offset.y += self.spacing + item.rect.height
            else:
                offset.x += self.spacing + item.rect.width


@dataclass
class Fill(Layout):
    """
    Layout items to be the equally sized in a single row or column.
    """

    direction: Direction = Direction.VERTICAL

    def __call__(self, bounds: FRect | Rect, items: LayoutItems, **kwargs) -> None:
        if items:
            if self.direction == Direction.VERTICAL:
                offset = Vector2(0, bounds.height // len(items))
                slot = pygame.Rect(0, 0, bounds.width, offset.y)
            else:
                offset = Vector2(bounds.width // len(items), 0)
                slot = pygame.Rect(0, 0, offset.x, bounds.height)

            for i, item in enumerate(items):
                slot.topleft = cast(tuple[int, int], offset * i)
                item.rect.update(Vector2(bounds.topleft) + slot.topleft, slot.size)
