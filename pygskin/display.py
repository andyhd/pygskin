import pygame

from pygskin import ecs


class Display(ecs.System):
    sprites = pygame.sprite.LayeredUpdates()

    def __init__(self, **options) -> None:
        size = options.setdefault("size", (800, 600))
        self.window = pygame.display.set_mode(
            size,
            options.setdefault("flags", 0),
        )
        self.surface = pygame.Surface(size).convert_alpha()
        pygame.display.set_caption(options.setdefault("title", "pygame window"))

    def update(self, *args, **kwargs):
        self.surface.fill("black")
        self.sprites.draw(self.surface)
        self.window.blit(self.surface, (0, 0))
        pygame.display.flip()
