from __future__ import annotations

import pygame


class MetaWindow(type):
    fullscreen: bool = False
    rect: pygame.Rect = pygame.Rect(0, 0, 800, 600)

    @property
    def size(cls) -> tuple[int, int]:
        return cls.rect.size

    @size.setter
    def size(cls, value: tuple[int, int]) -> None:
        cls.rect.size = value

    @property
    def surface(cls) -> pygame.Surface:
        if not hasattr(cls, "_surface"):
            flags = 0
            flags &= pygame.FULLSCREEN if cls.fullscreen else 0
            cls._surface = pygame.display.set_mode(cls.rect.size, flags)
            pygame.display.set_caption(cls.title)
        return cls._surface

    @property
    def title(cls) -> str:
        if not hasattr(cls, "_title"):
            cls._title = "Pygame Project"
        return cls._title

    @title.setter
    def title(cls, title: str) -> None:
        cls._title = title
        pygame.display.set_caption(title)

    @property
    def width(cls) -> int:
        return cls.rect.width

    @property
    def height(cls) -> int:
        return cls.rect.height


class Window(metaclass=MetaWindow):
    fullscreen: bool = False
