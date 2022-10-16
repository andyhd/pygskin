from typing import Callable

import pygame

from pygskin.input import InputHandler


class Window(InputHandler):
    def __init__(self, size: tuple[int, int], **config) -> None:
        pygame.init()
        pygame.font.init()
        self.window = pygame.display.set_mode(size)
        pygame.display.set_caption(config.setdefault("title", "pygame window"))
        self.clock = pygame.time.Clock()
        self.fps = config.setdefault("fps", 60)
        self.running = False
        self.config = config
        self.main_loop: Callable | None = None

    def blit(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        self.window.blit(surface, rect)

    def quit(self) -> None:
        self.running = False

    def run(self) -> None:
        self.running = True
        while self.running:
            dt = self.clock.tick(self.fps)
            self.update(dt)
            pygame.display.flip()
        pygame.quit()

    def update(self, dt: float) -> None:
        super().update(dt)
        if callable(self.main_loop):
            self.main_loop(dt)
