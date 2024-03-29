from typing import Iterable

import pygame
from pygame.sprite import Sprite

from pygskin import ecs


class Parallax(ecs.Entity, Sprite):
    # TODO use a LayeredUpdates sprite group
    def __init__(
        self,
        rect: pygame.Rect,
        layers: list[tuple[float, Sprite]],
    ) -> None:
        ecs.Entity.__init__(self)
        Sprite.__init__(self)
        self.rect = pygame.Rect(rect)
        self.layers = []
        for divisor, layer in layers:
            if isinstance(layer, pygame.Surface):
                sprite = Sprite()
                sprite.image = layer
                sprite.rect = pygame.FRect(layer.get_rect())
                layer = sprite
            self.layers.append((divisor, layer))
        self._image = None

    def force_redraw(self) -> None:
        self._image = None

    def add_layer(self, layer: Sprite | pygame.Surface, divisor: float) -> None:
        if isinstance(layer, pygame.Surface):
            sprite = Sprite()
            sprite.image = layer
            sprite.rect = pygame.FRect(layer.get_rect())
            layer = sprite
        self.layers.append((divisor, layer))
        self.force_redraw()

    def scroll(self, vector: Iterable[float]) -> None:
        vector = pygame.math.Vector2(*vector)
        if vector:
            self.force_redraw()
        for divisor, layer in self.layers:
            if divisor != 0:
                layer.rect.center += vector / divisor
            if layer.rect.left > self.rect.left + layer.rect.width:
                layer.rect.right = self.rect.left
            if layer.rect.right < self.rect.right - layer.rect.width:
                layer.rect.left = self.rect.right

    def draw(self, surface: pygame.Surface) -> None:
        surface.set_clip(self.rect)
        for _, layer in self.layers:
            surface.blit(layer.image, pygame.Rect(*map(int, layer.rect)))
            if layer.rect.left > self.rect.left:
                surface.blit(
                    layer.image,
                    pygame.Rect(*map(int, layer.rect.move(-layer.rect.width, 0))),
                )
            if layer.rect.right < self.rect.right:
                surface.blit(
                    layer.image,
                    pygame.Rect(*map(int, layer.rect.move(layer.rect.width, 0))),
                )
        surface.set_clip(None)

    @property
    def image(self) -> pygame.Surface:
        if not self._image:
            self._image = pygame.Surface(self.rect.size).convert_alpha()
            self._image.fill((0, 0, 0, 0))
            self.scroll((0, 0))
            self.draw(self._image)
        return self._image
