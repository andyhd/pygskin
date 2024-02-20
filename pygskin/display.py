import pygame

from pygskin import ecs


class Display(ecs.System):
    sprites = pygame.sprite.LayeredUpdates()
    surface: pygame.Surface
    rect: pygame.Rect
    options: dict

    def __init__(self, **options) -> None:
        Display.rect = pygame.Rect((0, 0), options.setdefault("size", (800, 600)))
        if surface := pygame.display.get_surface():
            Display.surface = surface
        else:
            Display.surface = pygame.display.set_mode(
                Display.rect.size,
                options.setdefault("flags", 0),
            )
        Display.surface.convert_alpha()
        Display.set_caption(options.setdefault("title", "pygame window"))
        Display.options = options

    @classmethod
    def get_caption(cls) -> str:
        return pygame.display.get_caption()

    @classmethod
    def set_caption(cls, caption: str) -> None:
        pygame.display.set_caption(caption)

    @classmethod
    def update(cls, *args, **kwargs):
        cls.surface.fill(cls.options.get("background", "black"))
        cls.sprites.draw(cls.surface)
        pygame.display.flip()
