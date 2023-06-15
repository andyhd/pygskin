from typing import Iterable

import pygame

from pygskin import ecs
from pygskin.pubsub import message


class TickHandler(message):
    pass


on_tick = TickHandler


class Clock(ecs.System):
    def __init__(self, **options) -> None:
        self._clock = pygame.time.Clock()
        self.fps = options.get("fps", 0)
        self.ms_since_last_tick = 0

    def filter(self, entity: ecs.Entity) -> bool:
        return entity.has(TickHandler)

    def update(self, entities: Iterable[ecs.Entity], **kwargs) -> None:
        self.ms_since_last_tick = self._clock.tick(self.fps)
        super().update(entities, **kwargs)

    def update_entity(self, entity: ecs.Entity, **kwargs) -> None:
        entity.TickHandler(self.ms_since_last_tick, **kwargs)


# class IntervalSystem(TickSystem):
#     interval = 0

#     def __init__(self, **options):
#         super().__init__(**options)
#         self.timer = self.interval

#     def should_update(self, **kwargs) -> bool:
#         self.timer -= self.ms_since_last_tick
#         if self.timer <= 0:
#             self.timer = self.interval
#             return True
#         return False
