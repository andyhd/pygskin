from typing import Iterable

import pygame
from pygame.sprite import Sprite


class Parallax(Sprite):
    # TODO use a LayeredUpdates sprite group
    def __init__(
        self,
        rect: pygame.Rect,
        layers: list[tuple[float, Sprite]],
    ) -> None:
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
        self.layers.sort()
        self._image = None

    def add_layer(self, layer: Sprite | pygame.Surface, divisor: float) -> None:
        if isinstance(layer, pygame.Surface):
            sprite = Sprite()
            sprite.image = layer
            sprite.rect = pygame.FRect(layer.get_rect())
            layer = sprite
        self.layers.append((divisor, layer))
        self.layers.sort()

    def scroll(self, vector: Iterable[float]) -> None:
        if not self._image:
            self._image = pygame.Surface(self.rect.size).convert_alpha()
        self._image.set_clip(self.rect)
        for divisor, layer in self.layers:
            if divisor != 0:
                layer.rect.center += pygame.math.Vector2(*vector) / divisor
            if layer.rect.left > self.rect.left + layer.rect.width:
                layer.rect.right = self.rect.left
            if layer.rect.right < self.rect.right - layer.rect.width:
                layer.rect.left = self.rect.right
            self._image.blit(layer.image, pygame.Rect(*map(int, layer.rect)))
            if layer.rect.left > self.rect.left:
                self._image.blit(
                    layer.image,
                    pygame.Rect(*map(int, layer.rect.move(-layer.rect.width, 0))),
                )
            if layer.rect.right < self.rect.right:
                self._image.blit(
                    layer.image,
                    pygame.Rect(*map(int, layer.rect.move(layer.rect.width, 0))),
                )

    @property
    def image(self) -> pygame.Surface:
        if not self._image:
            self.scroll((0, 0))
        return self._image
