from typing import Protocol

import pygame


class Drawable(Protocol):
    image: pygame.Surface
    rect: pygame.rect.Rect

    def draw(self, surface: pygame.Surface) -> pygame.rect.Rect:
        return surface.blit(self.image, self.rect)


class Updatable(Protocol):
    def update(self, dt: float) -> None:
        ...
