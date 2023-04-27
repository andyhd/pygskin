import pygame

from pygskin import ecs
from pygskin.display import Display
from pygskin.pubsub import message


class Screen(pygame.sprite.Sprite, ecs.Entity):
    def __init__(self, **config) -> None:
        pygame.sprite.Sprite.__init__(self, Display.sprites)
        ecs.Entity.__init__(self)
        self.rect = pygame.Rect((0, 0), config.setdefault("size", (800, 600)))
        self.image = pygame.Surface(self.rect.size).convert_alpha()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={id(self)}>"

    @message
    def exit(self, *args) -> None:
        self.kill()
        ecs.Entity.instances.remove(self)

    def update(self) -> None:
        pass
