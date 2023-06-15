import pygame

from pygskin import ecs


class Display(ecs.System):
    sprites = pygame.sprite.LayeredUpdates()

    def __init__(self, **options) -> None:
        size = options.setdefault("size", (800, 600))
        self.surface = pygame.display.set_mode(
            size,
            options.setdefault("flags", 0),
        )
        self.surface.convert_alpha()
        pygame.display.set_caption(options.setdefault("title", "pygame window"))

    def update(self, *args, **kwargs):
        self.surface.fill("black")
        self.sprites.draw(self.surface)
        pygame.display.flip()
