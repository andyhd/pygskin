import pygame

from pygskin.ecs import System
from pygskin.text import Text


class DisplaySystem(System):
    sprite_group = pygame.sprite.LayeredUpdates()

    def __init__(self, **options) -> None:
        size = options.setdefault("size", (800, 600))
        self.window = pygame.display.set_mode(size)
        self.surface = pygame.Surface(size).convert_alpha()
        pygame.display.set_caption(options.setdefault("title", "pygame window"))
        watermark= Text(
            "Powered by Pygskin",
            color=pygame.Color(255, 255, 255),
            font_size=21,
        )
        watermark.image.set_alpha(127)
        watermark.rect.bottom = size[1] - 20
        watermark.rect.right = size[0] - 20
        self.sprite_group.add(watermark, layer=1)

    def update(self, *args, **kwargs):
        self.surface.fill("black")
        self.sprite_group.draw(self.surface)
        self.window.blit(self.surface, (0, 0))
        pygame.display.flip()
