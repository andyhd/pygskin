import pygame

from pygskin.ecs import Entity, System
from pygskin.ecs.components.tick import TickHandler


class TickSystem(System):
    query = Entity.has(TickHandler)

    def __init__(self, **options) -> None:
        self.clock = pygame.time.Clock()
        self.fps = options.get("fps", 60)
        self.ms_since_last_tick = 0

    def tick(self) -> int:
        self.ms_since_last_tick = self.clock.tick(self.fps)
        return self.ms_since_last_tick

    def update(self, entities, **kwargs) -> None:
        self.tick()
        super().update(entities, ms_since_last_tick=self.ms_since_last_tick, **kwargs)

    def update_entity(self, entity, ms_since_last_tick=0, **kwargs) -> None:
        entity.TickHandler.on_tick(ms_since_last_tick)


class IntervalSystem(TickSystem):
    interval = 0

    def __init__(self, **options):
        super().__init__(**options)
        self.timer = self.interval

    def tick(self):
        self.timer -= super().tick()

    def update(self, entities, **kwargs):
        self.tick()
        if self.timer <= 0:
            self.timer = self.interval
            super().update(entities, **kwargs)
