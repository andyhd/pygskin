import pygame

from pygskin.input_handler import InputHandler
from pygskin.interfaces import Drawable
from pygskin.interfaces import Updatable


class Screen(pygame.Surface, Updatable, Drawable, InputHandler):
    def update(self, dt: float) -> None:
        super().update(dt)
