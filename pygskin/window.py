from __future__ import annotations

from typing import Callable

import pygame

from pygskin.input import InputHandler


class Window(InputHandler):
    def __init__(self, size: tuple[int, int], **config) -> None:
        pygame.init()
        pygame.font.init()
        self.surface = pygame.display.set_mode(size)
        pygame.display.set_caption(config.setdefault("title", "pygame window"))
        self.clock = pygame.time.Clock()
        self.fps = config.setdefault("fps", 60)
        self.running = False
        self.config = config
        self.main_loop: Callable | None = None

    def quit(self) -> None:
        self.running = False

    def run(self) -> None:
        self.running = True
        while self.running:
            self.tick()
        pygame.quit()

    def tick(self) -> int:
        pygame.display.flip()
        dt = self.clock.tick(self.fps)
        bg = self.config.get("background")
        if bg:
            if isinstance(bg, (pygame.Color, str)):
                self.surface.fill(bg)
            elif isinstance(bg, pygame.Surface):
                self.surface.blit(bg, (0, 0))
        super().update(dt)
        if callable(self.main_loop):
            self.main_loop(dt)
        return dt

    def __enter__(self) -> Window:
        self.running = True
        return self

    def __exit__(self, *args, **kwargs) -> None:
        pygame.quit()
