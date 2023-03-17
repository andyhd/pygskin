from __future__ import annotations

import pygame

from pygskin import ecs
from pygskin.ecs.components import EventMap
from pygskin.ecs.systems import DisplaySystem
from pygskin.ecs.systems import EventSystem
from pygskin.events import Quit


class Window(ecs.Entity, ecs.Container):
    def __init__(self, **config) -> None:
        super().__init__()
        self.running = False
        self.config = config
        self.event_map = EventMap({Quit(): self.quit})
        self.systems.extend(
            [
                DisplaySystem(**config),
                EventSystem(),
            ]
        )

    def quit(self, *args) -> None:
        self.running = False

    def run(self) -> None:
        self.running = True
        while self.running:
            self.update()
        pygame.quit()
