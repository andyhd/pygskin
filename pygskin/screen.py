import pygame

from pygskin import pubsub
from pygskin.input import InputHandler


class Screen(InputHandler):
    def draw(self, surface: pygame.Surface) -> list[pygame.Rect]:
        return []

    @pubsub.message
    def enter(self) -> None:
        pass

    @pubsub.message
    def exit(self) -> None:
        pass
