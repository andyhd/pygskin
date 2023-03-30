import pygame

from pygskin.ecs import Entity
from pygskin.ecs import System
from pygskin.ecs.components.tick import TickHandler


class TickSystem(System):
    query = Entity.has(TickHandler)

    def __init__(self, **options) -> None:
        self.clock = pygame.time.Clock()
        self.fps = options.get("fps", 0)
        self.ms_since_last_tick = 0

    def tick(self) -> int:
        self.ms_since_last_tick = self.clock.tick(self.fps)
        return self.ms_since_last_tick

    def should_update(self, **kwargs) -> bool:
        return True

    def update(self, entities, **kwargs) -> None:
        self.tick()
        if self.should_update(**kwargs):
            super().update(entities, **kwargs)

    def update_entity(self, entity, **kwargs) -> None:
        entity.TickHandler.on_tick(self.ms_since_last_tick)


class IntervalSystem(TickSystem):
    interval = 0

    def __init__(self, **options):
        super().__init__(**options)
        self.timer = self.interval

    def should_update(self, **kwargs) -> bool:
        self.timer -= self.ms_since_last_tick
        if self.timer <= 0:
            self.timer = self.interval
            return True
        return False
