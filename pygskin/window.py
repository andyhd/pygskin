from __future__ import annotations

import asyncio

import pygame

from pygskin import ecs
from pygskin.clock import Clock
from pygskin.display import Display


class Window(ecs.Entity, ecs.Container):
    def __init__(self, **config) -> None:
        super().__init__()
        self.running = False
        self.config = config
        self.systems.extend(
            [
                Display(**config),
                Clock(**config),
            ]
        )

    async def main_loop(self) -> None:
        self.running = True
        while self.running:
            events = list(pygame.event.get())

            if any(event.type == pygame.QUIT for event in events):
                self.running = False

            self.update(events=events)
            await asyncio.sleep(0)
        pygame.quit()

    def run(self) -> None:
        asyncio.run(self.main_loop())
