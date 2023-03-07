import pygame

from pygskin.ecs import System


class DisplaySystem(System):
    sprite_group = pygame.sprite.LayeredUpdates()

    def __init__(self, **options) -> None:
        size = options.setdefault("size", (800, 600))
        self.window = pygame.display.set_mode(size)
        self.surface = pygame.Surface(size).convert_alpha()
        pygame.display.set_caption(options.setdefault("title", "pygame window"))

    def update(self, *args, **kwargs):
        self.surface.fill("black")
        self.sprite_group.draw(self.surface)
        self.window.blit(self.surface, (0, 0))
        pygame.display.flip()
