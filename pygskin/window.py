from __future__ import annotations

import asyncio

import pygame

from pygskin import ecs
from pygskin.display import Display
from pygskin.events import EventSystem
from pygskin.events import Quit


class Window(ecs.Entity, ecs.Container):
    def __init__(self, **config) -> None:
        super().__init__()
        self.running = False
        self.config = config
        Quit.subscribe(self.quit)
        self.systems.extend(
            [
                Display(**config),
                EventSystem(),
            ]
        )

    def quit(self, *args) -> None:
        self.running = False

    async def main_loop(self) -> None:
        self.running = True
        while self.running:
            self.update()
            await asyncio.sleep(0)
        pygame.quit()

    def run(self) -> None:
        asyncio.run(self.main_loop())
