from __future__ import annotations

from collections.abc import Callable

import pygame


class LazyImage:
    def __init__(self, fn: Callable[..., pygame.Surface]) -> None:
        self.fn = fn

    def __get__(self, obj, cls_=None) -> pygame.Surface:
        if not hasattr(obj, "_image") and callable(self.fn):
            self.obj = obj
            obj._image = self.fn(obj)

        return obj._image

    def __del__(self) -> None:
        if hasattr(self, "obj") and hasattr(self.obj, "_image"):
            del self.obj._image
