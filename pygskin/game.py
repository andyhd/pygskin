from __future__ import annotations

import asyncio

import pygame
import pygame.locals as pg
from pygame.event import Event

from pygskin.clock import Clock
from pygskin.screen import Screen
from pygskin.screen import ScreenManager
from pygskin.window import Window


class GameLoop:
    def __init__(self) -> None:
        self.running = True

    def start(self) -> None:
        pygame.init()
        self.setup()
        asyncio.run(self._main_loop())

    async def _main_loop(self) -> None:
        while self.running:
            self.update(list(pygame.event.get()))
            self.draw()
            await asyncio.sleep(0)
        self.stop()
        pygame.quit()

    def setup(self) -> None:
        ...

    def update(self, events: list[pygame.event.Event]) -> None:
        ...

    def draw(self) -> None:
        ...

    def stop(self) -> None:
        ...


class Game(GameLoop):
    def __init__(
        self,
        initial_screen: type[Screen],
        window_size: tuple[int, int] = (800, 600),
        window_title: str = "Pygame Project",
    ) -> None:
        super().__init__()
        self.initial_screen = initial_screen
        self.window_size = window_size
        self.window_title = window_title

    def setup(self) -> None:
        Window.rect.size = self.window_size
        Window.title = self.window_title
        self.screen = ScreenManager(self.initial_screen)

    def update(self, events: list[Event]) -> None:
        Clock.tick()
        if any(event.type == pg.QUIT for event in events):
            self.running = False
        self.screen.update(events)

    def draw(self) -> None:
        self.screen.draw(Window.surface)
        pygame.display.flip()


if __name__ == "__main__":
    GameLoop().start()
