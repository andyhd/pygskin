import pygame
from pygskin import pubsub
from pygskin.input import InputHandler


class Screen(InputHandler):
    def draw(self, surface: pygame.Surface) -> list[pygame.Rect]:
        return []

    @property
    def enter(self) -> pubsub.Message:
        if not hasattr(self, "_enter"):
            setattr(self, "_enter", pubsub.Message())
        return getattr(self, "_enter")

    @property
    def exit(self) -> pubsub.Message:
        if not hasattr(self, "_exit"):
            setattr(self, "_exit", pubsub.Message())
        return getattr(self, "_exit")
